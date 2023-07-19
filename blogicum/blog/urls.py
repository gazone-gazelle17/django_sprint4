from django.urls import include, path

from . import views

app_name = 'blog'

posts_urls = [
    path('create/', views.PostCreateView.as_view(), name='create_post'),
    path('<int:pk>/', views.post_detail, name='post_detail'),
    path('<int:pk>/edit/', views.PostUpdateView.as_view(), name='edit_post'),
    path('<int:pk>/delete/',
         views.PostDeleteView.as_view(), name='delete_post'),
    path('<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('<int:post_id>/edit_comment/<int:comment_id>/',
         views.edit_comment, name='edit_comment'),
    path('<int:post_id>/delete_comment/<int:comment_id>/',
         views.comment_delete,
         name='delete_comment'),
]

profile_urls = [
    path('edit/', views.user_profile_update, name='edit_profile'),
    path('<username>/', views.UserListView.as_view(), name='profile'),
]

urlpatterns = [
    path('posts/', include(posts_urls)),
    path('profile/', include(profile_urls)),
    path('category/<slug:category_slug>/',
         views.category_posts,
         name='category_posts'),
    path('',
         views.index,
         name='index'),
]
