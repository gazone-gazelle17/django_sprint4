from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, UpdateUserForm

User = get_user_model()


def index(request):
    posts = Post.objects.annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date'
    ).filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
    )
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if not request.user.is_authenticated or post.author != request.user:
        post = get_object_or_404(
            Post,
            pk=pk,
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        )
    form = CommentForm()
    context = {
        'post': post,
        'comments': post.comments.all(),
        'form': form,
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True)
    post_list = Post.objects.filter(
        category=category,
        pub_date__lte=timezone.now(),
        is_published=True,
    ).order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'category_slug': category_slug,
        'category': category
    }
    return render(request, 'blog/category.html', context)


class UserListView(ListView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    paginate_by = 10
    form = UpdateUserForm()

    def get_queryset(self):
        author = get_object_or_404(User,
                                   username=self.kwargs['username']
                                   )
        if author == self.request.user:
            return Post.objects.prefetch_related('author',
                                                 'location',
                                                 'category'
                                                 ).filter(author=author
            ).order_by('-pub_date').annotate(
            comment_count=Count('comments'))
        else:
            return Post.objects.prefetch_related(
                'author',
                'location',
                'category'
            ).filter(author=author,
                         is_published=True,
                         pub_date__lte=timezone.now(),
                         category__is_published=True
                         ).order_by('-pub_date').annotate(
                comment_count=Count('comments'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(User,
                                               username=self.kwargs['username']
                                               )
        queryset = self.get_queryset()
        total_count = queryset.count()
        context['total_count'] = total_count
        return context


class PostCreateView(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        post = form.save(commit=False)
        if post.pub_date > timezone.now():
            post.is_published = False
        else:
            post.is_published = True
        form.instance.author = self.request.user
        post.save()
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('blog:index')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        username = self.request.user.username
        return reverse_lazy('blog:profile', kwargs={'username': username})


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != self.request.user:
            return redirect('blog:post_detail', pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.object.pk})


class PostDeleteView(DeleteView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('blog:index')
        get_object_or_404(Post, pk=self.kwargs['pk'],
                          author=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        post = self.object
        return reverse_lazy('blog:category_posts',
                            kwargs={'category_slug': post.category.slug})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', pk=post.id)


@login_required
def edit_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id, post=post)
    if comment.author != request.user:
        return redirect('blog:post_detail', pk=post.id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.save()
    return render(request, 'blog/comment.html',
                  {'form': form, 'comment': comment})


@login_required
def comment_delete(request, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment,
                                id=comment_id,
                                post=post,
                                author=request.user)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', pk=post.id)
    return render(request, 'blog/comment.html', {'comment': comment})


@login_required
def user_profile_update(request):
    if request.method == 'POST' and request.user.is_authenticated:
        username = request.POST['username']
        email = request.POST['email']
        user = request.user
        user.username = username
        user.email = email
        user.first_name = request.POST['first_name']
        user.last_name = request.POST['last_name']
        user.save()
        return redirect('blog:index')
    else:
        if request.user.is_authenticated:
            user = request.user
            return render(request, 'blog/user.html',
                          {'form': UpdateUserForm()})
