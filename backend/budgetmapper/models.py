from io import BufferedIOBase, RawIOBase

import pykakasi
import shortuuidfield
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify
from polymorphic.models import PolymorphicModel
from rest_framework.authtoken.models import Token


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class CurrentDateTimeField(models.DateTimeField):
    def __init__(self, *args, **kwargs):
        super(CurrentDateTimeField, self).__init__(
            *args, **dict(kwargs, default=timezone.now, editable=False, null=False)
        )


class AutoUpdateCurrentDateTimeField(CurrentDateTimeField):
    def pre_save(self, model_instance, add):
        val = timezone.now()
        setattr(model_instance, self.attname, val)
        return val


kks = pykakasi.kakasi()


def jp_slugify(name: str) -> str:
    return slugify("-".join(d["hepburn"] for d in kks.convert(name)))


class JpSlugField(models.SlugField):
    def __init__(self, *args, **kwargs):
        super(JpSlugField, self).__init__(*args, **dict(kwargs, null=True, blank=True))

    def pre_save(self, model_instance, add):
        val = getattr(model_instance, self.attname)
        if val is None or len(val) == 0:
            val = jp_slugify(model_instance.name)
            setattr(model_instance, self.attname, val)
        return val


class NameField(models.TextField):
    def __init__(self, *args, **kwargs):
        super(NameField, self).__init__(*args, **dict(kwargs, null=True, db_index=True))


class IdField(shortuuidfield.ShortUUIDField):
    def __init__(self, *args, **kwargs):
        super(IdField, self).__init__(*args, **dict(kwargs, editable=False))


class PkField(IdField):
    def __init__(self, *args, **kwargs):
        super(PkField, self).__init__(*args, **dict(kwargs, primary_key=True))


class BudgetAmountField(models.FloatField):
    ...


class LatitudeField(models.FloatField):
    def __init__(self, *args, **kwargs):
        super(LatitudeField, self).__init__(
            *args, **dict(kwargs, validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)], null=True)
        )


class LongitudeField(models.FloatField):
    def __init__(self, *args, **kwargs):
        super(LongitudeField, self).__init__(
            *args, **dict(kwargs, validators=[MinValueValidator(0.0), MaxValueValidator(180.0)], null=True)
        )


def get_default_level_name_list():
    return ["款", "項", "目", "事業", "節", "節細"]


class LevelNameListField(ArrayField):
    def __init__(self, *args, **kwargs):
        super(LevelNameListField, self).__init__(
            *args,
            **dict(kwargs, base_field=models.CharField(max_length=255), default=get_default_level_name_list, null=True),
        )


class Government(models.Model):
    id = PkField()
    name = NameField()
    slug = JpSlugField(unique=True)
    latitude = LatitudeField()
    longitude = LongitudeField()
    created_at = CurrentDateTimeField()
    updated_at = AutoUpdateCurrentDateTimeField()


class ClassificationSystem(models.Model):
    id = PkField()
    name = NameField()
    slug = JpSlugField(unique=True)
    level_names = LevelNameListField()
    created_at = CurrentDateTimeField()
    updated_at = AutoUpdateCurrentDateTimeField()

    @property
    def roots(self) -> models.QuerySet:
        return Classification.objects.filter(classification_system=self, parent=None).order_by("code")

    @property
    def leaves(self) -> models.QuerySet:
        return Classification.objects.filter(
            ~models.Exists(Classification.objects.filter(classification_system=self, parent=models.OuterRef("pk"))),
            classification_system=self,
        )

    def __iterate_classifications_sub(self, buf):
        is_leaf = True
        for d in Classification.objects.filter(parent=buf[-1]):
            is_leaf = False
            yield from self.__iterate_classifications_sub(buf + [d])
        if is_leaf:
            yield buf

    def iterate_classifications(self):
        for r in self.roots:
            yield from self.__iterate_classifications_sub([r])


class Classification(models.Model):
    id = PkField()
    name = NameField()
    code = models.CharField(max_length=64, null=True, db_index=True)
    classification_system = models.ForeignKey(ClassificationSystem, on_delete=models.CASCADE)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    created_at = CurrentDateTimeField()
    updated_at = AutoUpdateCurrentDateTimeField()

    @property
    def level(self) -> int:
        if self.parent is None:
            return 0
        return self.parent.level + 1

    def clean(self) -> None:
        if self.parent is not None:
            if self.parent.classification_system != self.classification_system:
                raise ValidationError(
                    {"classification_system": "classification_system must be the same as that of parent"}
                )

    @property
    def direct_children(self) -> models.QuerySet:
        return Classification.objects.filter(parent=self).order_by("code")


class Budget(models.Model):
    id = PkField()
    name = NameField()
    slug = JpSlugField(unique=True)
    year = models.IntegerField(null=False, db_index=True)
    subtitle = models.TextField(null=True)
    classification_system = models.ForeignKey(ClassificationSystem, on_delete=models.CASCADE, db_index=True, null=False)
    government = models.ForeignKey(Government, on_delete=models.CASCADE, db_index=True, null=False)
    created_at = CurrentDateTimeField()
    updated_at = AutoUpdateCurrentDateTimeField()

    def get_value_of(self, classification: Classification) -> float:
        if self.classification_system != classification.classification_system:
            raise ValueError
        try:
            val = BudgetItemBase.objects.get(budget=self, classification=classification)
            return val.value
        except BudgetItemBase.DoesNotExist:
            return sum(self.get_value_of(c) for c in Classification.objects.filter(parent=classification))

    def iterate_items(self):
        for cl in self.classification_system.iterate_classifications():
            try:
                val = BudgetItemBase.objects.get(budget=self, classification=cl[-1])
                yield {"classifications": cl, "budget_item": val}
            except BudgetItemBase.DoesNotExist:
                yield {"classifications": cl, "budget_item": None}

    class Meta:
        indexes = [
            models.Index(fields=["government", "year"]),
        ]


class BudgetItemBase(PolymorphicModel):
    id = PkField()
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, db_index=True, null=False)
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE, db_index=True, null=False)
    created_at = CurrentDateTimeField()
    updated_at = AutoUpdateCurrentDateTimeField()

    @property
    def value(self) -> float:
        raise NotImplementedError

    class Meta:
        unique_together = ("budget", "classification")

    def clean(self) -> None:
        if self.budget.classification_system != self.classification.classification_system:
            raise ValidationError(
                {
                    "budget": "classification_system should be the same as that of classification",
                    "classification": "classification_system should be the same as that of budget",
                }
            )


class AtomicBudgetItem(BudgetItemBase):
    amount = BudgetAmountField()

    @property
    def value(self) -> float:
        return float(self.amount)


class MappedBudgetItem(BudgetItemBase):
    mapped_budget = models.ForeignKey(Budget, db_index=True, on_delete=models.CASCADE, null=False)
    mapped_classifications = models.ManyToManyField(Classification, related_name="mapping_classifications")

    @property
    def value(self) -> float:
        return sum(self.mapped_budget.get_value_of(c) for c in self.mapped_classifications.all())


class Blob(models.Model):
    id = PkField()
    name = NameField()
    created_at = CurrentDateTimeField()
    updated_at = AutoUpdateCurrentDateTimeField()

    @classmethod
    def write(cls, data: RawIOBase, name: str = None, chunk_size: int = 65536) -> None:
        instance = cls(name=name)
        instance.save()
        idx = 0
        while True:
            buf = data.read(chunk_size)
            if len(buf) == 0:
                break
            BlobChunk(blob=instance, index=idx, body=buf).save()
            idx += 1
        return instance


class BlobChunk(models.Model):
    id = PkField()
    blob = models.ForeignKey(Blob, on_delete=models.CASCADE, db_index=False, null=False)
    index = models.PositiveIntegerField(db_index=False)
    body = models.BinaryField(db_index=False)

    class Meta:
        unique_together = ("blob", "index")


class BlobReader(BufferedIOBase):
    def __init__(self, blob: Blob):
        self._fp = BlobChunk.objects.filter(blob=blob).order_by("index")
        self._buffer = b''
        self._gen = self._next()

    def _next(self) -> BlobChunk:
        for d in self._fp:
            yield d

    def read(self, size: int = -1) -> bytes:
        while size == -1 or len(self._buffer) < size:
            try:
                self._buffer += next(self._gen).body
            except StopIteration:
                break
        if size >= 0:
            retval = self._buffer[:size]
            self._buffer = self._buffer[size:]
        else:
            retval = self._buffer
            self._buffer = b""
        return retval
