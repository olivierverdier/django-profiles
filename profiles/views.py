"""
Views for creating, editing and viewing site-specific user profiles.

"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic import create_update, list_detail

from profiles import utils




def create_profile(request, form_class=None, success_url=None,
                   template_name='profiles/create_profile.html',
                   extra_context=None):
    """
    Create a profile for the current user, if one doesn't already
    exist.
    
    If the user already has a profile, as determined by
    ``request.user.get_profile()``, a redirect will be issued to the
    :view:`profiles.views.edit_profile` view. If no profile model has
    been specified in the ``AUTH_PROFILE_MODULE`` setting,
    ``django.contrib.auth.models.SiteProfileNotAvailable`` will be
    raised.
    
    **Optional arguments:**
    
    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``form_class``
        The form class to use for validating and creating the user
        profile. This form class must define a method named
        ``save()``, implementing the same argument signature as the
        ``save()`` method of a standard Django ``ModelForm`` (this
        view will call ``save(commit=False)`` to obtain the profile
        object, and fill in the user before the final save). If the
        profile object includes many-to-many relations, the convention
        established by ``ModelForm`` of using a method named
        ``save_m2m()`` will be used, and so your form class should
        also define this method.
        
        If this argument is not supplied, this view will use a
        ``ModelForm`` automatically generated from the model specified
        by ``AUTH_PROFILE_MODULE``.
    
    ``success_url``
        The URL to redirect to after successful profile creation. If
        this argument is not supplied, this will default to 
        ``profile.get_absolute_url()``.

    ``template_name``
        The template to use when displaying the profile-creation
        form. If not supplied, this will default to
        :template:`profiles/create_profile.html`.
    
    **Context:**
    
    ``form``
        The profile-creation form.
    
    **Template:**
    
    ``template_name`` keyword argument, or
    :template:`profiles/create_profile.html`.
    
    """
    try:
        profile_obj = request.user.get_profile()
        return redirect('profiles_edit_profile')
    except ObjectDoesNotExist:
        pass
    
    
    if form_class is None:
        form_class = utils.get_profile_form()

    return create_update.create_object(request, form_class=form_class(request.user), extra_context=extra_context, template_name=template_name, post_save_redirect=success_url)

create_profile = login_required(create_profile)

def edit_profile(request, form_class=None, success_url=None,
                 template_name='profiles/edit_profile.html',
                 extra_context=None):
    """
    Edit the current user's profile.
    
    If the user does not already have a profile (as determined by
    ``User.get_profile()``), a redirect will be issued to the
    :view:`profiles.views.create_profile` view; if no profile model
    has been specified in the ``AUTH_PROFILE_MODULE`` setting,
    ``django.contrib.auth.models.SiteProfileNotAvailable`` will be
    raised.
    
    **Optional arguments:**
    
    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``form_class``
        The form class to use for validating and editing the user
        profile. This form class must operate similarly to a standard
        Django ``ModelForm`` in that it must accept an instance of the
        object to be edited as the keyword argument ``instance`` to
        its constructor, and it must implement a method named
        ``save()`` which will save the updates to the object. If this
        argument is not specified, this view will use a ``ModelForm``
        generated from the model specified in the
        ``AUTH_PROFILE_MODULE`` setting.
    
    ``success_url``
        The URL to redirect to after successful profile creation. If
        this argument is not supplied, this will default to 
        ``profile.get_absolute_url()``.
    
    ``template_name``
        The template to use when displaying the profile-editing
        form. If not specified, this will default to
        :template:`profiles/edit_profile.html`.
    
    **Context:**
    
    ``form``
        The form for editing the profile.
        
    ``profile``
         The user's current profile.
    
    **Template:**
    
    ``template_name`` keyword argument or
    :template:`profiles/edit_profile.html`.
    
    """
    try:
        profile_obj = request.user.get_profile()
    except ObjectDoesNotExist:
        return redirect('profiles_create_profile')
    
    if success_url is None:
        success_url = reverse('profiles_profile_detail',
                              kwargs={ 'username': request.user.username })
    elif callable(success_url):
        success_url = success_url(profile_obj)
   
    return create_update.update_object(request, object_id=profile_obj.id, form_class=form_class, extra_context=extra_context, template_name=template_name, post_save_redirect=success_url)

edit_profile = login_required(edit_profile)

def profile_detail(request, username, public_profile_field=None,
                   template_name='profiles/profile_detail.html',
                   extra_context=None):
    """
    Detail view of a user's profile.
    
    If no profile model has been specified in the
    ``AUTH_PROFILE_MODULE`` setting,
    ``django.contrib.auth.models.SiteProfileNotAvailable`` will be
    raised.
    
    If the user has not yet created a profile, ``Http404`` will be
    raised.
    
    **Required arguments:**
    
    ``username``
        The username of the user whose profile is being displayed.
    
    **Optional arguments:**

    ``extra_context``
        A dictionary of variables to add to the template context. Any
        callable object in this dictionary will be called to produce
        the end result which appears in the context.

    ``public_profile_field``
        The name of a ``BooleanField`` on the profile model; if the
        value of that field on the user's profile is ``False``, the
        ``profile`` variable in the template will be ``None``. Use
        this feature to allow users to mark their profiles as not
        being publicly viewable.
        
        If this argument is not specified, it will be assumed that all
        users' profiles are publicly viewable.
    
    ``template_name``
        The name of the template to use for displaying the profile. If
        not specified, this will default to
        :template:`profiles/profile_detail.html`.
    
    **Context:**
    
    ``profile``
        The user's profile, or ``None`` if the user's profile is not
        publicly viewable (see the description of
        ``public_profile_field`` above).
    
    **Template:**
    
    ``template_name`` keyword argument or
    :template:`profiles/profile_detail.html`.
    
    """
    user = get_object_or_404(User, username=username)
    try:
        profile_obj = user.get_profile()
    except ObjectDoesNotExist:
        if request.user == user: #If we are trying to view our own nonexistent profile, redirect to profile creation
            return redirect(create_profile)
        raise Http404
    if public_profile_field is not None and \
       not getattr(profile_obj, public_profile_field):
       if user == request.user: #If the user is trying to view their own (invisible) profile
           return redirect(edit_profile) 
       else: 
           profile_obj = None

    return list_detail.object_detail(request, extra_context=extra_context, queryset=profile_obj._default_manager.all(), object_id=profile_obj.id, template_name=template_name, template_object_name='profile')

def profile_list(request, public_profile_field=None,
                 template_name='profiles/profile_list.html', **kwargs):
    """
    A list of user profiles.
    
    If no profile model has been specified in the
    ``AUTH_PROFILE_MODULE`` setting,
    ``django.contrib.auth.models.SiteProfileNotAvailable`` will be
    raised.

    **Optional arguments:**

    ``public_profile_field``
        The name of a ``BooleanField`` on the profile model; if the
        value of that field on a user's profile is ``False``, that
        profile will be excluded from the list. Use this feature to
        allow users to mark their profiles as not being publicly
        viewable.
        
        If this argument is not specified, it will be assumed that all
        users' profiles are publicly viewable.
    
    ``template_name``
        The name of the template to use for displaying the profiles. If
        not specified, this will default to
        :template:`profiles/profile_list.html`.

    Additionally, all arguments accepted by the
    :view:`django.views.generic.list_detail.object_list` generic view
    will be accepted here, and applied in the same fashion. 
    If ``queryset`` is not provided, it will be set to the ``QuerySet`` of the
    model specified by the ``AUTH_PROFILE_MODULE`` setting, optionally
    filtered to remove non-publicly-viewable profiles.
    
    **Context:**
    
    Same as the :view:`django.views.generic.list_detail.object_list`
    generic view.
    
    **Template:**
    
    ``template_name`` keyword argument or
    :template:`profiles/profile_list.html`.
    
    """
    profile_model = utils.get_profile_model()
    queryset = kwargs.get('queryset')
    if not queryset:
        queryset = profile_model._default_manager.all()
        if public_profile_field is not None:
            queryset = queryset.filter(**{ public_profile_field: True })
        kwargs['queryset'] = queryset
    return list_detail.object_list(request, template_name=template_name, **kwargs)
