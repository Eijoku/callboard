import random

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import AdvertisementForm, ConfirmationForm, EmailAuthenticationForm, ResponseForm, SignUpForm
from .models import Advertisement, AdvertisementCategory, RegistrationConfirmation, Response


class AdvertisementListView(ListView):
    model = Advertisement
    template_name = "board/advertisement_list.html"
    context_object_name = "advertisements"
    paginate_by = 10

    def get_queryset(self):
        queryset = Advertisement.objects.select_related("author").annotate(response_count=Count("responses"))
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category=category)
        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = AdvertisementCategory.choices
        context["selected_category"] = self.request.GET.get("category", "")
        return context


class AdvertisementDetailView(DetailView):
    model = Advertisement
    template_name = "board/advertisement_detail.html"
    context_object_name = "advertisement"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        advertisement = self.object
        if user.is_authenticated and user != advertisement.author:
            context["response_form"] = kwargs.get("response_form") or ResponseForm()
        return context


class AdvertisementCreateView(CreateView):
    model = Advertisement
    form_class = AdvertisementForm
    template_name = "board/advertisement_form.html"
    success_url = reverse_lazy("board:advertisement_list")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("board:login")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class AdvertisementUpdateView(UpdateView):
    model = Advertisement
    form_class = AdvertisementForm
    template_name = "board/advertisement_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("board:login")
        advertisement = self.get_object()
        if advertisement.author != request.user:
            return HttpResponseForbidden("Вы не можете редактировать это объявление.")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.object.get_absolute_url()


def signup_view(request):
    initial = {"email": request.session.get("confirmation_email", "")}
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password1"]
            User.objects.filter(email__iexact=email, is_active=False).delete()
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                is_active=False,
            )
            code = f"{random.randint(0, 999999):06d}"
            RegistrationConfirmation.objects.update_or_create(user=user, defaults={"code": code})
            send_mail(
                subject="Код подтверждения регистрации",
                message=f"Ваш код подтверждения: {code}",
                from_email=None,
                recipient_list=[email],
            )
            request.session["confirmation_email"] = email
            messages.success(request, "Код подтверждения отправлен на указанный e-mail.")
            return redirect("board:confirm_registration")
    else:
        form = SignUpForm(initial=initial)
    return render(request, "board/signup.html", {"form": form})


def confirm_registration_view(request):
    initial = {"email": request.session.get("confirmation_email", "")}
    if request.method == "POST":
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].lower()
            code = form.cleaned_data["code"]
            user = get_object_or_404(User, email__iexact=email)
            confirmation = get_object_or_404(RegistrationConfirmation, user=user)
            if confirmation.is_expired():
                confirmation.delete()
                user.delete()
                messages.error(request, "Код подтверждения истёк. Зарегистрируйтесь повторно.")
                return redirect("board:signup")
            if confirmation.code != code:
                form.add_error("code", "Неверный код подтверждения.")
            else:
                user.is_active = True
                user.save(update_fields=["is_active"])
                confirmation.delete()
                login(request, user)
                request.session.pop("confirmation_email", None)
                messages.success(request, "Регистрация подтверждена.")
                return redirect("board:advertisement_list")
    else:
        form = ConfirmationForm(initial=initial)
    return render(request, "board/confirm_registration.html", {"form": form})


@login_required
def create_response_view(request, pk):
    advertisement = get_object_or_404(Advertisement.objects.select_related("author"), pk=pk)
    if advertisement.author == request.user:
        messages.error(request, "Нельзя откликаться на собственное объявление.")
        return redirect("board:advertisement_detail", pk=pk)

    form = ResponseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        response, created = Response.objects.get_or_create(
            advertisement=advertisement,
            author=request.user,
            defaults={"text": form.cleaned_data["text"]},
        )
        if created:
            send_mail(
                subject="Новый отклик на объявление",
                message=(
                    f"На ваше объявление '{advertisement.title}' пришёл отклик.\n\n"
                    f"Текст отклика:\n{response.text}"
                ),
                from_email=None,
                recipient_list=[advertisement.author.email],
            )
            messages.success(request, "Отклик отправлен.")
            return redirect("board:advertisement_detail", pk=pk)
        form.add_error(None, "Вы уже оставляли отклик на это объявление.")

    return render(
        request,
        "board/advertisement_detail.html",
        {"advertisement": advertisement, "response_form": form},
    )


@login_required
def response_list_view(request):
    advertisements = Advertisement.objects.filter(author=request.user).order_by("title")
    selected_advertisement = request.GET.get("advertisement")
    responses = Response.objects.filter(advertisement__author=request.user).select_related(
        "advertisement", "author"
    )
    if selected_advertisement:
        responses = responses.filter(advertisement_id=selected_advertisement)
    return render(
        request,
        "board/response_list.html",
        {
            "responses": responses,
            "advertisements": advertisements,
            "selected_advertisement": selected_advertisement,
        },
    )


@login_required
def accept_response_view(request, pk):
    response = get_object_or_404(Response.objects.select_related("advertisement", "author"), pk=pk)
    if response.advertisement.author != request.user:
        return HttpResponseForbidden("Вы не можете принимать этот отклик.")
    response.status = Response.Status.ACCEPTED
    response.save(update_fields=["status"])
    send_mail(
        subject="Ваш отклик принят",
        message=f"Ваш отклик на объявление '{response.advertisement.title}' был принят.",
        from_email=None,
        recipient_list=[response.author.email],
    )
    messages.success(request, "Отклик принят, уведомление отправлено.")
    return redirect("board:response_list")


@login_required
def delete_response_view(request, pk):
    response = get_object_or_404(Response.objects.select_related("advertisement"), pk=pk)
    if response.advertisement.author != request.user:
        return HttpResponseForbidden("Вы не можете удалить этот отклик.")
    response.delete()
    messages.success(request, "Отклик удалён.")
    return redirect("board:response_list")


def login_view(request):
    form = EmailAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("board:advertisement_list")
    return render(request, "board/login.html", {"form": form})
