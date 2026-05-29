from .models import SiteBranding


def active_branding(request):
    branding = SiteBranding.objects.filter(is_active=True).order_by("-updated_at").first()
    return {"active_branding": branding}
