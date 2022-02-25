import base64
import json
from abc import abstractmethod
from io import BufferedIOBase, BytesIO, RawIOBase

import pykakasi
import shortuuidfield
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db.models.signals import post_delete, post_save
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
            *args,
            **dict(
                kwargs,
                validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
                null=True,
            ),
        )


class LongitudeField(models.FloatField):
    def __init__(self, *args, **kwargs):
        super(LongitudeField, self).__init__(
            *args,
            **dict(
                kwargs,
                validators=[MinValueValidator(0.0), MaxValueValidator(180.0)],
                null=True,
            ),
        )


def get_default_level_name_list():
    return ["款", "項", "目", "事業", "節", "節細"]


class LevelNameListField(ArrayField):
    def __init__(self, *args, **kwargs):
        super(LevelNameListField, self).__init__(
            *args,
            **dict(
                kwargs,
                base_field=models.CharField(max_length=255),
                default=get_default_level_name_list,
                null=True,
            ),
        )


class ItemOrderField(models.IntegerField):
    def __init__(self, *args, **kwargs):
        super(ItemOrderField, self).__init__(*args, **dict(kwargs, null=True, db_index=True))

    def pre_save(self, model_instance, add):
        val = getattr(model_instance, self.attname)
        if val is None:
            qs = Classification.objects.filter(classification_system=model_instance.classification_system).order_by(
                "-item_order"
            )
            if qs.count() == 0:
                val = 0
            else:
                val = qs[0].item_order + 1
            setattr(model_instance, self.attname, val)
        return val


class ColorCodeField(models.CharField):
    def __init__(self, *args, **kwargs):
        super(ColorCodeField, self).__init__(
            *args,
            **dict(
                kwargs,
                max_length=8,
                validators=[
                    RegexValidator(
                        regex=r'^#(?:[0-9a-fA-F]{3}){1,2}$',
                        message="invalid_colorcode_format",
                        code='invalid_colorcode_format',
                    )
                ],
                null=True,
                db_index=False,
            ),
        )


class ImageTypeField(models.CharField):
    def __init__(self, *args, **kwargs):
        super(ImageTypeField, self).__init__(
            *args,
            **dict(
                kwargs,
                max_length=8,
                choices=(("svg+xml", "svg+xml"), ("jpeg", "jpeg"), ("png", "png"), ("gif", "gif")),
                db_index=False,
                null=False,
            ),
        )


class IconImage(models.Model):
    id = PkField()
    name = NameField()
    slug = JpSlugField(unique=True)
    image_type = ImageTypeField()
    body = models.BinaryField(db_index=False)
    created_at = CurrentDateTimeField()
    updated_at = AutoUpdateCurrentDateTimeField()

    def to_data_uri(self) -> str:
        return f'data:image/{self.image_type};base64,{base64.standard_b64encode(self.body).decode("utf-8")}'

    @classmethod
    def get_default_icon(cls) -> "IconImage":
        return cls.objects.get_or_create(
            slug="default-icon",
            defaults={
                "name": "default icon",
                "image_type": "svg+xml",
                "body": b'<svg version="1.1" id="Ebene_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.'
                b'w3.org/1999/xlink" x="0px" y="0px" width="100px" height="100px" viewBox="0 0 100 100" enable-backgr'
                b'ound="new 0 0 100 100" xml:space="preserve"><circle fill="#B2B2B2" cx="50" cy="50" r="50"/><g><path'
                b' d="M46.745,79.538c-3.866-0.402-8.458-1.449-12.324-3.705l2.255-6.444c2.819,2.095,6.686,3.786,10.391'
                b',4.35l1.208-22.876c-5.961-5.075-12.244-10.391-12.244-18.769c0-8.539,6.283-13.21,13.936-13.774l0.483'
                b'-8.78h5.316l-0.483,9.021c2.578,0.322,5.559,1.128,8.861,2.497l-1.853,5.639c-2.015-1.047-4.753-1.933-'
                b'7.331-2.336l-1.208,21.588c6.122,5.155,12.646,10.713,12.646,19.655c0,8.457-6.041,13.29-14.419,14.016'
                b'l-0.563,10.149h-5.155L46.745,79.538z M48.759,41.599l0.886-17.238c-3.544,0.645-6.364,2.9-6.364,7.169'
                b'C43.281,35.477,45.618,38.619,48.759,41.599z M53.27,55.132l-0.967,18.606c4.189-0.805,6.848-3.705,6.8'
                b'48-7.894S56.653,58.354,53.27,55.132z"/></g></svg>',
            },
        )[0]


class Government(models.Model):
    id = PkField()
    name = NameField()
    slug = JpSlugField(unique=True)
    latitude = LatitudeField()
    longitude = LongitudeField()
    primary_color_code = ColorCodeField()
    secondary_color_code = ColorCodeField()
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
        return Classification.objects.filter(classification_system=self, parent=None).order_by("item_order")

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
    icon = models.ForeignKey(IconImage, blank=True, null=True, on_delete=models.SET_NULL, default=None)
    item_order = ItemOrderField()
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
        return Classification.objects.filter(parent=self).order_by("item_order")

    def get_icon_id(self):
        return self.icon.id if self.icon is not None else IconImage.get_default_icon().id

    class Meta:
        unique_together = ("classification_system", "item_order")


class BudgetBase(PolymorphicModel):
    id = PkField()
    name = NameField()
    slug = JpSlugField(unique=True)
    subtitle = models.TextField(null=True)
    classification_system = models.ForeignKey(ClassificationSystem, on_delete=models.CASCADE, db_index=True, null=False)
    created_at = CurrentDateTimeField()
    updated_at = AutoUpdateCurrentDateTimeField()

    def get_amount_of(self, classification: Classification) -> float:
        if self.classification_system != classification.classification_system:
            raise ValueError
        try:
            val = BudgetItemBase.objects.get(budget=self, classification=classification)
            return val.amount
        except BudgetItemBase.DoesNotExist:
            return sum(self.get_amount_of(c) for c in Classification.objects.filter(parent=classification))

    def iterate_items(self):
        for cl in self.classification_system.iterate_classifications():
            try:
                val = BudgetItemBase.objects.get(budget=self, classification=cl[-1])
                yield {"classifications": cl, "budget_item": val}
            except BudgetItemBase.DoesNotExist:
                yield {"classifications": cl, "budget_item": None}

    @property
    @abstractmethod
    def year(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def government(self):
        raise NotImplementedError


class BasicBudget(BudgetBase):
    year_value = models.IntegerField(null=False, db_index=True)
    government_value = models.ForeignKey(Government, on_delete=models.CASCADE, db_index=True, null=False)

    @property
    def year(self):
        return self.year_value

    @property
    def government(self):
        return self.government_value

    class Meta:
        indexes = [
            models.Index(fields=["government_value", "year_value"]),
        ]


class MappedBudget(BudgetBase):
    source_budget = models.ForeignKey(
        BudgetBase, related_name="mapped_budget", db_index=True, on_delete=models.CASCADE, null=False
    )

    @property
    def year(self):
        return self.source_budget.year

    @property
    def government(self):
        return self.source_budget.government

    def bulk_create(self, data):
        qs = MappedBudgetItem.objects.filter(budget=self)
        known_classes = set()
        with transaction.atomic():
            for d in data:
                if len(d["source_classifications"]) == 0:
                    continue
                mbi, created = qs.get_or_create(classification_id=d["classification"], defaults={"budget": self})
                if created:
                    mbi.source_classifications.set(d["source_classifications"])
                    mbi.save()
                elif set(c.id for c in mbi.source_classifications.all()) != set(d["source_classifications"]):
                    mbi.source_classifications.set(d["source_classifications"])
                    mbi.save()
                known_classes.add(d["classification"])
            qs.exclude(classification__in=known_classes).delete()
        return qs.all()


class BudgetItemBase(PolymorphicModel):
    id = PkField()
    budget = models.ForeignKey(BudgetBase, on_delete=models.CASCADE, db_index=True, null=False)
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE, db_index=True, null=False)
    created_at = CurrentDateTimeField()
    updated_at = AutoUpdateCurrentDateTimeField()

    @property
    def amount(self) -> float:
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
    value = BudgetAmountField()

    @property
    def amount(self) -> float:
        return float(self.value)


class MappedBudgetItem(BudgetItemBase):
    source_classifications = models.ManyToManyField(Classification, related_name="mapping_classifications")

    @property
    def amount(self) -> float:
        return sum(self.budget.source_budget.get_amount_of(c) for c in self.source_classifications.all())


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
    blob = models.ForeignKey(Blob, on_delete=models.CASCADE, db_index=True, null=False)
    index = models.PositiveIntegerField(db_index=False)
    body = models.BinaryField(db_index=False)

    class Meta:
        unique_together = ("blob", "index")


class BlobReader(BufferedIOBase):
    def __init__(self, blob: Blob):
        self._fp = BlobChunk.objects.filter(blob=blob).order_by("index")
        self._buffer = b""
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


class WdmmgTreeCache(models.Model):
    id = PkField()
    blob = models.ForeignKey(Blob, on_delete=models.CASCADE, db_index=False, null=False)
    budget = models.OneToOneField(BudgetBase, on_delete=models.CASCADE, null=False)
    created_at = CurrentDateTimeField()
    updated_at = AutoUpdateCurrentDateTimeField()

    @classmethod
    def cache_tree(cls, data, budget):
        blob = Blob.write(BytesIO(json.dumps(data).encode("utf-8")), name=budget.name)
        try:
            cache = cls.objects.get(budget=budget)
            cache.blob = blob
        except cls.DoesNotExist:
            cache = cls(budget=budget, blob=blob)
        cache.save()
        return cache

    @classmethod
    def get_or_none(cls, budget):
        try:
            cache = cls.objects.get(budget=budget)
        except cls.DoesNotExist:
            return None
        if cache.updated_at > budget.updated_at:
            return json.load(BlobReader(cache.blob))
        return None


class DefaultBudget(models.Model):
    id = PkField()
    government = models.OneToOneField(Government, on_delete=models.CASCADE, db_index=True, null=False, unique=True)
    budget = models.OneToOneField(BudgetBase, on_delete=models.CASCADE, null=False, db_index=False)
    created_at = CurrentDateTimeField()
    updated_at = AutoUpdateCurrentDateTimeField()

    def save(self, *args, **kwargs):
        if self.budget.government.id != self.government.id:
            raise ValidationError("A budget must blongs to specified government.")

        super(DefaultBudget, self).save(*args, **kwargs)


@receiver(post_save, sender=AtomicBudgetItem)
def touch_budget_on_save_atomic_budget_item(sender, instance=None, **kwargs):
    if instance is not None:
        instance.budget.save()


@receiver(post_delete, sender=AtomicBudgetItem)
def touch_budget_on_delete_atomic_budget_item(sender, instance=None, **kwargs):
    if instance is not None:
        instance.budget.save()


@receiver(post_save, sender=MappedBudgetItem)
def touch_budget_on_save_mapped_budget_item(sender, instance=None, **kwargs):
    if instance is not None:
        instance.budget.save()


@receiver(post_delete, sender=MappedBudgetItem)
def touch_budget_on_delete_mapped_budget_item(sender, instance=None, **kwargs):
    if instance is not None:
        instance.budget.save()


@receiver(post_save, sender=ClassificationSystem)
def touch_budget_on_classification_system_save(sender, instance=None, **kwargs):
    if instance is not None:
        for budget in BudgetBase.objects.filter(classification_system=instance):
            budget.save()


@receiver(post_save, sender=Classification)
def touch_classification_system_on_classification_save(sender, instance=None, **kwargs):
    if instance is not None:
        instance.classification_system.save()


@receiver(post_delete, sender=Classification)
def touch_classification_system_on_delete_classification(sender, instance=None, **kwargs):
    if instance is not None:
        instance.classification_system.save()


@receiver(post_save, sender=BasicBudget)
def touch_mapped_budget_on_budget_save(sender, instance=None, **kwargs):
    if isinstance is not None:
        for budget in MappedBudget.objects.filter(source_budget=instance):
            budget.save()
