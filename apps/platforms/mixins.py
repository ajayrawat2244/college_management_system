# apps/platforms/mixins.py
"""
CollegeScopedMixin
------------------
Inherit this in every ModelViewSet (or APIView) that operates within a
college tenant. It:

  1. Enforces tenant resolution (request.college must be set).
  2. Automatically filters all querysets to the current college.
  3. Automatically injects college into serializer save calls.
  4. Provides ``get_college()`` shortcut.

Usage::

    class StudentProfileViewSet(CollegeScopedMixin, ModelViewSet):
        serializer_class = StudentProfileSerializer
        queryset = StudentProfile.objects.all()   # filtered automatically
"""

from rest_framework.exceptions import PermissionDenied


class CollegeScopedMixin:
    """
    Mixin for all views that are scoped to a single college tenant.
    Must be listed BEFORE any ViewSet/APIView base class.
    """

    def get_college(self):
        if not self.request.college:
            raise PermissionDenied(
                "College tenant could not be resolved. "
                "Provide the X-College-ID header or use a valid subdomain."
            )
        return self.request.college

    def get_queryset(self):
        qs = super().get_queryset()
        college = self.get_college()
        # Only filter if the model actually has a 'college' field
        if hasattr(qs.model, "college_id"):
            return qs.filter(college=college)
        return qs

    def perform_create(self, serializer):
        serializer.save(college=self.get_college())

    def perform_update(self, serializer):
        serializer.save(college=self.get_college())
