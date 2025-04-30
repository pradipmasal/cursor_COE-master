from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Component, IssueRequest, UserProfile
from django.utils import timezone
from datetime import timedelta

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for password requirements
        self.fields['password1'].help_text = 'Your password must contain at least 8 characters and can\'t be entirely numeric.'
        self.fields['password2'].help_text = 'Enter the same password as before, for verification.'

class ComponentForm(forms.ModelForm):
    class Meta:
        model = Component
        fields = ['name', 'description', 'quantity']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class IssueRequestForm(forms.ModelForm):
    class Meta:
        model = IssueRequest
        fields = ['quantity', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter any additional information about your request'}),
            'quantity': forms.NumberInput(attrs={'min': 1, 'max': 100}),
        }
    
    def __init__(self, *args, **kwargs):
        self.component = kwargs.pop('component', None)
        super().__init__(*args, **kwargs)
        if self.component:
            self.fields['quantity'].widget.attrs['max'] = self.component.quantity
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if self.component:
            if quantity > self.component.quantity:
                raise forms.ValidationError(f'Only {self.component.quantity} items are available.')
            if quantity < 1:
                raise forms.ValidationError('Quantity must be at least 1.')
        return quantity

class IssueRequestUpdateForm(forms.ModelForm):
    class Meta:
        model = IssueRequest
        fields = ['status', 'notes', 'rejection_reason']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'rejection_reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter reason for rejection (required if rejecting)'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        rejection_reason = cleaned_data.get('rejection_reason')
        
        if status == 'rejected' and not rejection_reason:
            raise forms.ValidationError('Please provide a reason for rejection.')
        
        return cleaned_data

class DirectIssueComponentForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(userprofile__is_admin=False),
        empty_label="-- Select Student --",
        required=True
    )
    
    component = forms.ModelChoiceField(
        queryset=Component.objects.filter(available=True),
        empty_label="-- Select Component --",
        required=False
    )
    
    quantity = forms.IntegerField(
        min_value=1,
        required=False,
        widget=forms.NumberInput(attrs={'min': 1})
    )
    
    return_deadline = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add any additional notes (optional)'})
    )
    
    class Meta:
        model = IssueRequest
        fields = ['student', 'component', 'quantity', 'return_deadline', 'notes']
    
    def clean(self):
        cleaned_data = super().clean()
        component = cleaned_data.get('component')
        quantity = cleaned_data.get('quantity')
        
        if component and quantity:
            if quantity > component.quantity:
                raise forms.ValidationError(f'Only {component.quantity} items are available for {component.name}.')
        
        return cleaned_data
    
    def save(self, commit=True, admin=None):
        instance = super().save(commit=False)
        instance.status = 'approved'
        instance.request_date = timezone.now()
        instance.issue_date = timezone.now()
        instance.admin = admin
        
        if commit:
            instance.save()
            
            # Update component quantity
            component = instance.component
            component.quantity -= instance.quantity
            if component.quantity <= 0:
                component.available = False
            component.save()
        
        return instance 