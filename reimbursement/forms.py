import os
import json
from django import forms
from django.conf import settings
from django.forms import ModelForm
from django.template.defaultfilters import filesizeformat

from app.mixins import BootstrapFormMixin
from reimbursement.models import Reimbursement


class ReceiptSubmissionReceipt(BootstrapFormMixin, ModelForm):
    bootstrap_field_info = {
        "Upload your receipt": {
            "fields": [{"name": "receipt", "space": 12}],
        },
        "Where should we send you the money?": {
            "fields": [
                {"name": "paypal_email", "space": 12},
            ],
        },
        "Where are you travelling from?": {
            "fields": [
                {"name": "origin", "space": 12},
            ],
        },
    }

    def __init__(self, *args, **kwargs):
        super(ReceiptSubmissionReceipt, self).__init__(*args, **kwargs)
        self.fields["receipt"].required = True
        self.fields["paypal_email"].required = True

    def clean_paypal_email(self):
        paypal = self.cleaned_data.get("paypal_email", "")
        if not paypal:
            raise forms.ValidationError(
                "Please add PayPal so we can send you reimbursement"
            )
        return paypal

    def clean_receipt(self):
        receipt = self.cleaned_data["receipt"]
        size = getattr(receipt, "_size", 0)
        if size > settings.MAX_UPLOAD_SIZE:
            raise forms.ValidationError(
                "Please keep resume under %s. Current filesize %s"
                % (filesizeformat(settings.MAX_UPLOAD_SIZE), filesizeformat(size))
            )
        # # check if is pdf
        # if receipt and not receipt.name.endswith(".pdf"):
        #     raise forms.ValidationError("Please upload a PDF file")

        if(not receipt.name.endswith(".pdf")):
            raise forms.ValidationError("Please upload a PDF file")
        return receipt

    def clean_origin(self):
        origin = self.cleaned_data["origin"]
        # read from json file on local machine

        # actual file path
        dir_path = os.path.dirname(os.path.realpath(__file__))

        # get static relative path
        STATIC_ROOT = os.path.join(dir_path, "./static")
        # open relative file
        with open(os.path.join(STATIC_ROOT, "cities.json")) as f:
            countries = json.load(f)

            # check if is part of the list
            if origin not in countries:
                raise forms.ValidationError(
                    "Please select one of the dropdown options and don't forget to add commas"
                )
            return origin

    def save(self, commit=True):
        reimb = super(ReceiptSubmissionReceipt, self).save(commit=False)
        reimb.submit_receipt()
        if commit:
            reimb.save()
        return reimb

    class Meta:
        model = Reimbursement
        fields = (
            "paypal_email",
            "receipt",
            "origin",
        )
        widgets = {
            "origin": forms.TextInput(attrs={"autocomplete": "off"}),
        }

        labels = {"paypal_email": "PayPal email"}
        extensions = getattr(settings, "SUPPORTED_RESUME_EXTENSIONS", None)
        help_texts = {
            "paypal_email": 'We will send the reimbursement to this email. If you don\'t have a PayPal account, please \
                            create a free one <a target="_blank" href="https://www.paypal.com">here</a>.',
            "receipt": "Accepted file formats: %s"
            % (", ".join(extensions) if extensions else "Any"),
            "origin": "If you don’t see your city, choose the closest one! <br> Please type following this schema: \
                        <strong>city, province, country</strong>",
        }


class RejectReceiptForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(RejectReceiptForm, self).__init__(*args, **kwargs)
        self.fields["public_comment"].required = True

    class Meta:
        model = Reimbursement
        fields = ("public_comment",)
        labels = {"public_comment": "Why is this receipt being rejected?"}


class AcceptReceiptForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(AcceptReceiptForm, self).__init__(*args, **kwargs)
        self.fields["reimbursement_money"].required = True

    class Meta:
        model = Reimbursement
        fields = (
            "reimbursement_money",
            "origin",
        )
        labels = {"reimbursement_money": "Total cost in receipt"}

        widgets = {
            "origin": forms.TextInput(attrs={"autocomplete": "off"}),
        }


class ValidateReimbursementForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ValidateReimbursementForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Reimbursement
        fields = ()


class EditReimbursementForm(ModelForm):
    def __getitem__(self, item):
        item = super(EditReimbursementForm, self).__getitem__(item)
        # Hide reimbursement money if it has not been approved yet!
        if not self.instance.is_accepted() and item.name == "reimbursement_money":
            item.field.widget = forms.HiddenInput()
        else:
            item.field.required = True
        return item

    class Meta:
        model = Reimbursement
        fields = (
            "reimbursement_money",
            "expiration_time",
        )
        labels = {
            "reimbursement_money": "Amount to be reimbursed",
            "expiration_time": "When is the reimbursement expiring?",
        }


class DevpostValidationForm(BootstrapFormMixin, ModelForm):
    bootstrap_field_info = {
        "Devpost URL": {
            "fields": [{"name": "devpost", "space": 12}],
        },
    }

    def __init__(self, *args, **kwargs):
        super(DevpostValidationForm, self).__init__(*args, **kwargs)
        self.fields["devpost"].required = True

    class Meta:
        model = Reimbursement
        fields = ("devpost",)
        labels = {"devpost": "Devpost URL"}
        help_texts = {"devpost": "Please provide the URL of your Devpost project"}
        widgets = {
            "devpost": forms.TextInput(attrs={"autocomplete": "off", "placeholder": "https://devpost.com/software/..."}),
        }

    def clean_devpost(self):
        devpost = self.cleaned_data["devpost"]
        if not devpost:
            raise forms.ValidationError("Please provide a Devpost URL")
        if not devpost.startswith("https://devpost.com/software/"):
            raise forms.ValidationError("Please provide a valid Software Devpost URL that follows the structure: https://devpost.com/software/your-project-name")
        return devpost
