from django.db import models
from django.utils.timezone import now
from django.core.validators import MinValueValidator

LEVEL_100 = "100"
LEVEL_200 = "200"
LEVEL_300 = "300"
LEVEL_400 = "400"

LEVEL = (
    (LEVEL_100, "100"),
    (LEVEL_200, "200"),
    (LEVEL_300, "300"),
    (LEVEL_400, "400"),
)

class Session(models.Model):
    session = models.CharField(max_length=200, unique=True,null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    is_current_session = models.BooleanField(default=False)

    def __str__(self):
        return self.session

    def save(self, *args, **kwargs):
        if self.is_current_session:
            # Find the previous session
            previous_session = Session.objects.filter(is_current_session=True).exclude(id=self.id).first()
            if previous_session and now().date() > previous_session.end_date:
                # If the current date exceeds the end date of the previous session,
                # increment the level of all students
                students_to_increment = Student.objects.filter(level=previous_session.level)
                for student in students_to_increment:
                    student.increment_level()
        super().save(*args, **kwargs)

class Student(models.Model):
    name = models.TextField(max_length=100, unique=False)
    student_id = models.IntegerField(unique=True, blank=True, null=True)
    index_number = models.IntegerField(unique=True, blank=True, null=True)
    reference_number = models.IntegerField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=60, blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    level = models.CharField(max_length=25, choices=LEVEL, null=True)
    payment_balance = models.FloatField(default=0.0,null=True)

    def __str__(self):
        return self.name

    def increment_level(self):
        if self.level == LEVEL_100:
            self.level = LEVEL_200
        elif self.level == LEVEL_200:
            self.level = LEVEL_300
        elif self.level == LEVEL_300:
            self.level = LEVEL_400
        elif self.level == LEVEL_400:
            self.level = "Completed"

        if self.level != "Completed":
            self.save()


class LevelBill(models.Model):
    level_name = models.CharField(max_length=25, choices=LEVEL, null=True)
    academic_session = models.ForeignKey(Session, on_delete=models.CASCADE,null=True)
    academic_fees = models.FloatField(null=True)
    student_fees = models.FloatField(null=True)
    exams_fees = models.FloatField(null=True)

    def __str__(self):
        return f"Fees set for {self.level_name} in {self.academic_session}"
    
    def fees(self):
        payable_amount = self.academic_fees + self.student_fees + self.exams_fees
        return payable_amount

class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    levelBilling = models.ForeignKey(LevelBill, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE,null=True)
    paid_amount = models.FloatField(validators=[MinValueValidator(0.0)])
    bank_of_payment = models.TextField(max_length=100)
    draft_no = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField(default=now)

    def __str__(self):
        return f"{self.student} made a payment of {self.paid_amount} for {self.session}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update payment balance of the student after a successful payment
        total_fees = self.levelBilling.fees()
        total_paid = self.student.payments.aggregate(total_paid=models.Sum('paid_amount'))['total_paid'] or 0
        self.student.payment_balance = total_fees - total_paid
        self.student.save()
        