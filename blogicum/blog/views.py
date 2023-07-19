from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .forms import PostForm, CommentForm, UpdateUserForm
from .models import Post, Category, Comment, User
from .utils import paginate


def index(request):
    posts = Post.objects.select_related('category').annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date').filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True,
    )
    page_obj = paginate(request, posts)
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if not request.user.is_authenticated or post.author != request.user:
        post = get_object_or_404(
            Post.objects.select_related('category'),
            pk=pk,
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        )
    form = CommentForm()
    context = {
        'post': post,
        'comments': post.comments.all(
        ).select_related().order_by('created_at'),
        'form': form,
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True)
    posts = Post.objects.filter(
        category=category,
        pub_date__lte=timezone.now(),
        is_published=True,
    ).order_by('-pub_date').annotate(comment_count=Count('comments'))
    page_obj = paginate(request, posts)
    context = {
        'page_obj': page_obj,
        'category': category
    }
    return render(request, 'blog/category.html', context)


class UserListView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        author = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        if author == self.request.user:
            return Post.objects.select_related(
                'author',
                'location',
                'category'
            ).filter(
                author=author
            ).order_by(
                '-pub_date').annotate(comment_count=Count('comments'))
        else:
            return Post.objects.select_related(
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
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        post = form.save(commit=False)
        form.instance.author = self.request.user
        post.save()
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != self.request.user:
            return redirect('blog:post_detail', pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.object.pk})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != self.request.user:
            return redirect('blog:index')
        get_object_or_404(Post, pk=self.kwargs['pk'],
                          author=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:index')


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
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', pk=post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        comment.save()
    return render(request, 'blog/comment.html',
                  {'form': form, 'comment': comment})


@login_required
def comment_delete(request, post_id, comment_id):
    comment = get_object_or_404(Comment,
                                id=comment_id,
                                author=request.user)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', pk=post_id)
    return render(request, 'blog/comment.html', {'comment': comment})


@login_required
def user_profile_update(request):
    if request.method == 'POST':
        form = UpdateUserForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:index')
    else:
        form = UpdateUserForm()
    return render(request, 'blog/user.html', {'form': form})
