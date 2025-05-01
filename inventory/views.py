from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Count, Sum
from .models import Component, IssueRequest, UserProfile, User
from .forms import UserRegisterForm, ComponentForm, IssueRequestForm, IssueRequestUpdateForm, DirectIssueComponentForm
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from datetime import timedelta, date, datetime
from django.db import models
import barcode
from barcode.writer import ImageWriter
import os
from django.conf import settings
import json
from django.db import transaction



def is_admin(user):
    return user.userprofile.is_admin

def is_admin_or_staff(user):
    return user.userprofile.is_admin or user.is_staff

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_profile = UserProfile.objects.get(user=user)
            user_profile.is_admin = form.cleaned_data.get('is_admin', False)
            user_profile.save()
            login(request, user)
            messages.success(request, f'Account created successfully!')
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'inventory/register.html', {'form': form})

@login_required
def home(request):
    if request.user.userprofile.is_admin or request.user.is_staff:
        # Admin/Staff view
        components = Component.objects.all()
        pending_requests = IssueRequest.objects.filter(status='pending')
        issued_requests = IssueRequest.objects.filter(status='approved')
        users = User.objects.all()
        
        # Analytics data
        total_components = Component.objects.count()
        available_components = Component.objects.filter(available=True).count()
        unavailable_components = total_components - available_components
        
        # Request status distribution
        status_data = {
            'pending': IssueRequest.objects.filter(status='pending').count(),
            'approved': IssueRequest.objects.filter(status='approved').count(),
            'rejected': IssueRequest.objects.filter(status='rejected').count(),
            'returned': IssueRequest.objects.filter(status='returned').count()
        }
        
        # Daily requests for the last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        daily_requests = IssueRequest.objects.filter(
            request_date__gte=thirty_days_ago
        ).values('request_date__date').annotate(
            count=Count('id')
        ).order_by('request_date__date')
        
        # Top requested components
        top_components = IssueRequest.objects.values(
            'component__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Daily issues and returns for the last 30 days
        daily_issues = IssueRequest.objects.filter(
            issue_date__gte=thirty_days_ago,
            status='approved'
        ).values('issue_date__date').annotate(
            count=Count('id')
        ).order_by('issue_date__date')
        
        daily_returns = IssueRequest.objects.filter(
            return_date__gte=thirty_days_ago,
            status='returned'
        ).values('return_date__date').annotate(
            count=Count('id')
        ).order_by('return_date__date')
        
        # Format data for charts
        daily_requests_data = []
        for item in daily_requests:
            daily_requests_data.append({
                'date': item['request_date__date'].strftime('%Y-%m-%d'),
                'count': item['count']
            })

        daily_issues_data = []
        for item in daily_issues:
            daily_issues_data.append({
                'date': item['issue_date__date'].strftime('%Y-%m-%d'),
                'count': item['count']
            })

        daily_returns_data = []
        for item in daily_returns:
            daily_returns_data.append({
                'date': item['return_date__date'].strftime('%Y-%m-%d'),
                'count': item['count']
            })

        top_components_data = list(top_components.values('component__name', 'count'))

        context = {
            'components': components,
            'pending_requests': pending_requests,
            'issued_requests': issued_requests,
            'users': users,
            'search_query': request.GET.get('search', ''),
            'user_search_query': request.GET.get('user_search', ''),
            'issued_search_query': request.GET.get('issued_search', ''),
            # Analytics data
            'total_components': total_components,
            'available_components': available_components,
            'unavailable_components': unavailable_components,
            'status_data': status_data,
            'daily_requests': json.dumps(daily_requests_data),
            'daily_issues': json.dumps(daily_issues_data),
            'daily_returns': json.dumps(daily_returns_data),
            'top_components': json.dumps(top_components_data),
        }
        
        return render(request, 'inventory/admin_home.html', context)
    else:
        # Student view
        user = get_object_or_404(User, id=request.user.id)
        my_requests = IssueRequest.objects.filter(student=user)
        components = Component.objects.all()

    context = {
        'user': user,
        'my_requests': my_requests,
        'components': components
    }
        
    return render(request, 'inventory/student_home.html', context)

@user_passes_test(is_admin_or_staff)
@login_required
def add_component(request):
    if request.method == 'POST':
        form = ComponentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Component added successfully!')
            return redirect('home')
    else:
        form = ComponentForm()
    return render(request, 'inventory/add_component.html', {'form': form})

@user_passes_test(is_admin_or_staff)
@login_required
def edit_component(request, pk):
    component = get_object_or_404(Component, pk=pk)
    if request.method == 'POST':
        form = ComponentForm(request.POST, instance=component)
        if form.is_valid():
            form.save()
            messages.success(request, 'Component updated successfully!')
            return redirect('home')
    else:
        form = ComponentForm(instance=component)
    return render(request, 'inventory/edit_component.html', {'form': form, 'component': component})

@user_passes_test(is_admin_or_staff)
@login_required
def delete_component(request, pk):
    component = get_object_or_404(Component, pk=pk)
    if request.method == 'POST':
        component.delete()
        messages.success(request, 'Component deleted successfully!')
        return redirect('home')
    return render(request, 'inventory/delete_component.html', {'component': component})

@login_required
def request_component(request, pk):
    component = get_object_or_404(Component, pk=pk)
    
    # Check if component is available
    if not component.available or component.quantity <= 0:
        messages.error(request, 'This component is currently unavailable.')
        return redirect('home')
    
    if request.method == 'POST':
        form = IssueRequestForm(request.POST, component=component)
        if form.is_valid():
            issue_request = form.save(commit=False)
            issue_request.component = component
            issue_request.student = request.user
            issue_request.status = 'pending'
            issue_request.request_date = timezone.now()
            issue_request.save()
            messages.success(request, 'Request submitted successfully!')
            return redirect('home')
    else:
        form = IssueRequestForm(component=component)
    return render(request, 'inventory/request_component.html', {'form': form, 'component': component})

@user_passes_test(is_admin_or_staff)
@login_required
def update_request(request, pk):
    issue_request = get_object_or_404(IssueRequest, pk=pk)
    if request.method == 'POST':
        form = IssueRequestUpdateForm(request.POST, instance=issue_request)
        if form.is_valid():
            issue_request = form.save(commit=False)
            issue_request.admin = request.user
            if form.cleaned_data['status'] == 'approved':
                issue_request.issue_date = timezone.now()
                # Set return deadline to 7 days from issue date
                issue_request.return_deadline = issue_request.issue_date + timedelta(days=7)
            elif form.cleaned_data['status'] == 'returned':
                issue_request.return_date = timezone.now()
            issue_request.save()
            messages.success(request, 'Request updated successfully!')
            return redirect('home')
    else:
        form = IssueRequestUpdateForm(instance=issue_request)
    return render(request, 'inventory/update_request.html', {'form': form, 'issue_request': issue_request})

@user_passes_test(is_admin_or_staff)
@login_required
def generate_report(request):
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    components = Component.objects.all()
    requests = IssueRequest.objects.all()
    
    # Apply filters
    if search_query:
        components = components.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
        requests = requests.filter(
            Q(component__name__icontains=search_query) |
            Q(student__username__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    if date_from:
        requests = requests.filter(request_date__gte=date_from)
    
    if date_to:
        requests = requests.filter(request_date__lte=date_to)
    
    # Calculate statistics
    total_requests = requests.count()
    pending_requests = requests.filter(status='pending').count()
    approved_requests = requests.filter(status='approved').count()
    returned_requests = requests.filter(status='returned').count()
    
    # Calculate issued quantities for each component
    component_stats = {}
    for component in components:
        issued_quantity = IssueRequest.objects.filter(
            component=component,
            status='approved'
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        component_stats[component.id] = {
            'issued': issued_quantity,
            'total': component.quantity + issued_quantity
        }
    
    # Export functionality
    export_format = request.GET.get('export', '')
    if export_format:
        if export_format == 'pdf':
            return generate_pdf_report(components, requests, total_requests, pending_requests, approved_requests, returned_requests, component_stats)
        elif export_format == 'excel':
            return generate_excel_report(components, requests, total_requests, pending_requests, approved_requests, returned_requests, component_stats)
    
    return render(request, 'inventory/report.html', {
        'components': components,
        'requests': requests,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'returned_requests': returned_requests,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': IssueRequest.STATUS_CHOICES,
        'component_stats': component_stats
    })

def generate_pdf_report(components, requests, total_requests, pending_requests, approved_requests, returned_requests, component_stats):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from io import BytesIO
    
    # Create a BytesIO buffer to store the PDF
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12
    )
    
    # Create the content
    content = []
    
    # Add title
    content.append(Paragraph("Inventory Report", title_style))
    content.append(Spacer(1, 20))
    
    # Add statistics
    stats_data = [
        ['Total Components', 'Total Requests', 'Pending Requests', 'Approved Requests'],
        [str(len(components)), str(total_requests), str(pending_requests), str(approved_requests)]
    ]
    
    stats_table = Table(stats_data, colWidths=[2*inch]*4)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, 1), colors.lightblue),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.black),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, 1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    content.append(stats_table)
    content.append(Spacer(1, 20))
    
    # Add Component Details
    content.append(Paragraph("Component Details", heading_style))
    
    component_data = [['Component Name', 'Description', 'Barcode', 'Quantity', 'Status', 'Total Requests']]
    for component in components:
        stats = component_stats[component.id]
        component_data.append([
            component.name,
            component.description,
            component.barcode or 'No barcode',
            f"{stats['issued']}/{stats['total']}",
            'Available' if component.available else 'Unavailable',
            str(component.issuerequest_set.count())
        ])
    
    component_table = Table(component_data, colWidths=[1.2*inch, 1.8*inch, 1.2*inch, 1*inch, 1*inch, 1.2*inch])
    component_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    content.append(component_table)
    content.append(Spacer(1, 20))
    
    # Add Request Details
    content.append(Paragraph("Request Details", heading_style))
    
    request_data = [['Component', 'Requested By', 'Quantity', 'Status', 'Request Date', 'Issue Date', 'Return Deadline', 'Return Date']]
    for request in requests:
        request_data.append([
            request.component.name,
            request.student.username,
            str(request.quantity),
            request.status.title(),
            request.request_date.strftime("%B %d, %Y, %I:%M %p"),
            request.issue_date.strftime("%B %d, %Y, %I:%M %p") if request.issue_date else "-",
            request.return_deadline.strftime("%B %d, %Y, %I:%M %p") if request.return_deadline else "-",
            request.return_date.strftime("%B %d, %Y, %I:%M %p") if request.return_date else "-"
        ])
    
    request_table = Table(request_data, colWidths=[1.2*inch]*8)
    request_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    content.append(request_table)
    
    # Build the PDF
    doc.build(content)
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create the response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.pdf"'
    response.write(pdf)
    
    return response

def generate_excel_report(components, requests, total_requests, pending_requests, approved_requests, returned_requests, component_stats):
    import xlsxwriter
    from io import BytesIO
    
    # Create a BytesIO object to store the Excel file
    output = BytesIO()
    
    # Create a new Excel workbook and worksheet
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    
    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4e73df',
        'font_color': 'white',
        'border': 1
    })
    
    # Write headers
    headers = ['Component Name', 'Description', 'Barcode', 'Quantity', 'Status', 'Total Requests']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Write data
    for row, component in enumerate(components, start=1):
        stats = component_stats[component.id]
        worksheet.write(row, 0, component.name)
        worksheet.write(row, 1, component.description)
        worksheet.write(row, 2, component.barcode or 'No barcode')
        worksheet.write(row, 3, f"{stats['issued']}/{stats['total']}")
        worksheet.write(row, 4, 'Available' if component.available else 'Unavailable')
        worksheet.write(row, 5, component.issuerequest_set.count())
    
    # Add summary statistics
    worksheet.write(len(components) + 2, 0, 'Summary Statistics', header_format)
    worksheet.write(len(components) + 3, 0, 'Total Requests')
    worksheet.write(len(components) + 3, 1, total_requests)
    worksheet.write(len(components) + 4, 0, 'Pending Requests')
    worksheet.write(len(components) + 4, 1, pending_requests)
    worksheet.write(len(components) + 5, 0, 'Approved Requests')
    worksheet.write(len(components) + 5, 1, approved_requests)
    worksheet.write(len(components) + 6, 0, 'Returned Requests')
    worksheet.write(len(components) + 6, 1, returned_requests)
    
    # Close the workbook
    workbook.close()
    
    # Create the response
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="inventory_report.xlsx"'
    return response

@user_passes_test(is_admin_or_staff)
@login_required
def direct_issue_component(request):
    if request.method == 'POST':
        form = DirectIssueComponentForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            return_deadline = form.cleaned_data['return_deadline']
            notes = form.cleaned_data['notes']
            
            # Get bulk components data
            bulk_components = request.POST.getlist('bulk_components[]')
            bulk_quantities = request.POST.getlist('bulk_quantities[]')
            
            if bulk_components:
                # Bulk issue multiple components
                success_count = 0
                failed_components = []
                
                # Use transaction to ensure atomicity
                with transaction.atomic():
                    for i, component_id in enumerate(bulk_components):
                        try:
                            # Lock the component row
                            component = Component.objects.select_for_update().get(id=component_id)
                            quantity = int(bulk_quantities[i])
                            
                            # Check availability and quantity
                            if not component.available or quantity > component.quantity:
                                failed_components.append(component.name)
                                continue
                            
                            # Create issue request
                            issue_request = IssueRequest.objects.create(
                                student=student,
                                component=component,
                                quantity=quantity,
                                return_deadline=return_deadline,
                                notes=notes,
                                status='approved',
                                request_date=timezone.now(),
                                issue_date=timezone.now(),
                                admin=request.user
                            )
                            
                            # Update component quantity and availability
                            component.quantity -= quantity
                            if component.quantity <= 0:
                                component.available = False
                            component.save()
                            
                            success_count += 1
                        except (Component.DoesNotExist, ValueError, IndexError):
                            continue
                
                if success_count > 0:
                    messages.success(request, f'Successfully issued {success_count} components to {student.username}.')
                if failed_components:
                    messages.warning(request, f'Failed to issue components: {", ".join(failed_components)}')
                if success_count == 0 and not failed_components:
                    messages.error(request, 'Failed to issue any components.')
            else:
                # Single component issue
                try:
                    issue_request = form.save(admin=request.user)
                    messages.success(request, f'Component {issue_request.component.name} has been issued to {issue_request.student.username}.')
                except ValueError as e:
                    messages.error(request, str(e))
            
            return redirect('home')
    else:
        form = DirectIssueComponentForm()
    
    # Get all students (non-admin users)
    students = User.objects.filter(userprofile__is_admin=False)
    # Get all available components
    components = Component.objects.filter(available=True)
    
    return render(request, 'inventory/direct_issue_component.html', {
        'form': form,
        'students': students,
        'components': components
    })

@user_passes_test(is_admin_or_staff)
@login_required
def search_students(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse([], safe=False)
    
    students = User.objects.filter(
        Q(userprofile__is_admin=False) &
        (Q(username__icontains=query) | Q(email__icontains=query))
    )[:10]  # Limit to 10 results
    
    results = []
    for student in students:
        results.append({
            'id': student.id,
            'username': student.username,
            'email': student.email
        })
    
    return JsonResponse(results, safe=False)

@user_passes_test(is_admin_or_staff)
@login_required
def search_components(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse([], safe=False)
    
    components = Component.objects.filter(
        Q(available=True) &
        (Q(name__icontains=query) | Q(description__icontains=query))
    )[:10]  # Limit to 10 results
    
    results = []
    for component in components:
        results.append({
            'id': component.id,
            'name': component.name,
            'quantity': component.quantity
        })
    
    return JsonResponse(results, safe=False)

@user_passes_test(is_admin_or_staff)
@login_required
def scan_barcode(request):
    if request.method == 'POST':
        barcode = request.POST.get('barcode')
        try:
            component = Component.objects.get(barcode=barcode)
            # Get issue history for this component
            issue_history = IssueRequest.objects.filter(component=component).order_by('-request_date')
            return render(request, 'inventory/component_details.html', {
                'component': component,
                'issue_history': issue_history
            })
        except Component.DoesNotExist:
            messages.error(request, 'Component not found with this barcode.')
            return redirect('scan_barcode')
    return render(request, 'inventory/scan_barcode.html')

@user_passes_test(is_admin_or_staff)
@login_required
def generate_barcode(request, pk):
    component = get_object_or_404(Component, pk=pk)
    
    # Check if component has a barcode
    if not component.barcode:
        messages.error(request, 'Component does not have a barcode assigned.')
        return redirect('home')
    
    try:
        # Create barcode directory if it doesn't exist
        barcode_dir = os.path.join(settings.MEDIA_ROOT, 'barcodes')
        os.makedirs(barcode_dir, exist_ok=True)
        
        # Generate barcode
        barcode_path = os.path.join(barcode_dir, f'component_{component.id}')
        EAN = barcode.get_barcode_class('code128')
        ean = EAN(str(component.barcode), writer=ImageWriter())
        
        # Save the barcode with explicit path
        filename = ean.save(barcode_path)
        
        # Get the full path of the generated file
        full_path = os.path.join(barcode_dir, f'component_{component.id}.png')
        
        # Check if file exists
        if not os.path.exists(full_path):
            messages.error(request, f'Barcode file was not generated successfully. Path: {full_path}')
            return redirect('home')
        
        # Return the barcode image
        with open(full_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='image/png')
            response['Content-Disposition'] = f'attachment; filename="barcode_{component.barcode}.png"'
            return response
    except Exception as e:
        messages.error(request, f'Error generating barcode: {str(e)}')
        return redirect('home')

@user_passes_test(lambda u: u.is_superuser)
def delete_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Check if the user has any issued components
    issued_requests = IssueRequest.objects.filter(
        student=user,
        status='approved'
    )
    
    if issued_requests.exists():
        messages.error(request, f"User '{user.username}' cannot be deleted — they have issued components that need to be returned first.")
        return redirect('home')

    # Get all pending requests by this user
    pending_requests = IssueRequest.objects.filter(
        student=user,
        status='pending'
    )
    
    # Delete all pending requests
    pending_requests.delete()

    # Delete the user
    user.delete()
    messages.success(request, f"User '{user.username}' was deleted successfully.")
    return redirect('home')

@user_passes_test(is_admin)
def user_dashboard(request, user_id):
    user = get_object_or_404(User, id=user_id)
    issued_components = IssueRequest.objects.filter(student=user, status='approved')
    returned_components = IssueRequest.objects.filter(student=user, status='returned')

    context = {
        'user': user,
        'issued_components': issued_components,
        'returned_components': returned_components
    }
    return render(request, 'inventory/user_dashboard.html', context)

@user_passes_test(is_admin_or_staff)
@login_required
def analytics_dashboard(request):
    # Get inventory status data
    total_components = Component.objects.count()
    available_components = Component.objects.filter(available=True).count()
    unavailable_components = total_components - available_components

    # Get request status distribution
    status_data = {
        'pending': IssueRequest.objects.filter(status='pending').count(),
        'approved': IssueRequest.objects.filter(status='approved').count(),
        'rejected': IssueRequest.objects.filter(status='rejected').count(),
        'returned': IssueRequest.objects.filter(status='returned').count()
    }

    # Get request timeline data (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_requests = IssueRequest.objects.filter(
        request_date__gte=thirty_days_ago
    ).extra(
        select={'date': 'DATE(request_date)'}
    ).values('date').annotate(count=Count('id')).order_by('date')

    # Format daily requests data
    formatted_daily_requests = []
    for item in daily_requests:
        formatted_daily_requests.append({
            'date': item['date'].strftime('%Y-%m-%d'),
            'count': item['count']
        })

    # Get top requested components
    top_components = IssueRequest.objects.values('component__name').annotate(
        count=Count('id'),
        total_quantity=Sum('quantity')
    ).order_by('-count')[:10]

    # Get issue vs return timeline
    daily_issues = IssueRequest.objects.filter(
        status='approved',
        issue_date__gte=thirty_days_ago
    ).extra(
        select={'date': 'DATE(issue_date)'}
    ).values('date').annotate(count=Count('id')).order_by('date')

    # Format daily issues data
    formatted_daily_issues = []
    for item in daily_issues:
        formatted_daily_issues.append({
            'date': item['date'].strftime('%Y-%m-%d'),
            'count': item['count']
        })

    daily_returns = IssueRequest.objects.filter(
        status='returned',
        return_date__gte=thirty_days_ago
    ).extra(
        select={'date': 'DATE(return_date)'}
    ).values('date').annotate(count=Count('id')).order_by('date')

    # Format daily returns data
    formatted_daily_returns = []
    for item in daily_returns:
        formatted_daily_returns.append({
            'date': item['date'].strftime('%Y-%m-%d'),
            'count': item['count']
        })

    context = {
        'total_components': total_components,
        'available_components': available_components,
        'unavailable_components': unavailable_components,
        'status_data': status_data,
        'daily_requests': formatted_daily_requests,
        'top_components': list(top_components),
        'daily_issues': formatted_daily_issues,
        'daily_returns': formatted_daily_returns,
    }

    return render(request, 'inventory/analytics.html', context)

@user_passes_test(is_admin)
def user_dashboard(request, user_id):
    user = get_object_or_404(User, id=user_id)
    my_requests = IssueRequest.objects.filter(student=user)
    login_user = request.user


    context = {
        'user': user,
        'my_requests': my_requests,
        'login_user': login_user
    }
    return render(request, 'inventory/user_dashboard.html', context)    
