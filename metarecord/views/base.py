from rest_framework import filters, serializers

from metarecord.models import Attribute, AttributeValue


class AttributeFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        valid_attributes = {}

        for param, value in request.query_params.items():
            if not param.startswith('attributes__'):
                continue
            param = param[12:]
            try:
                attribute = Attribute.objects.get(identifier=param)
                valid_attributes[attribute] = value
            except Attribute.DoesNotExist:
                pass

        if not valid_attributes:
            return queryset

        for attribute, value in valid_attributes.items():
            attribute_values = AttributeValue.objects.filter(attribute=attribute, value=value)
            queryset = queryset.filter(attribute_values__in=attribute_values)

        return queryset


class BaseModelSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True, format='hex')


class StructuralElementSerializer(BaseModelSerializer):
    class Meta:
        exclude = ('attribute_values',)
        ordering = ('index',)

    attributes = serializers.SerializerMethodField()

    def get_attributes(self, instance):
        return {attr_val.attribute.identifier: attr_val.value for attr_val in instance.attribute_values.all()}


class DetailSerializerMixin:
    def get_serializer_class(self):
        if self.action == 'retrieve':
            try:
                return self.serializer_class_detail
            except AttributeError:
                pass

        return super().get_serializer_class()


class HexPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('pk_field', serializers.UUIDField(format='hex'))
        super().__init__(*args, **kwargs)
