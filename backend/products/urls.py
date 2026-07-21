from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    path('signup/', views.signup, name='signup'),
    
    path('login/', views.custom_login, name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    
    path('cart/', views.cart_view, name='cart'),
    
    path('remove-from-cart/<int:item_id>/', views.
    remove_from_cart, name='remove_from_cart'),
    
    path('update-cart/<int:item_id>/<str:action>/', views.update_cart_quantity, name='update_cart_quantity'),
    
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    
    path('checkout/', views.checkout, name='checkout'),
    
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    
    path('my-orders/', views.my_orders, name='my_orders'),
    
    path('about-us/', views.about_us, name='about_us'),
    
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),

    path('faq/', views.faq, name='faq'),
        
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
   
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
   
    path('my-admin-dashboard/', views.my_admin_dashboard, name='my_admin_dashboard'),
  
    path('update-order-status/<int:order_id>/<str:new_status>/', views.update_order_status, name='update_order_status'),
  
    path('admin-dashboard/products/', views.admin_product_list, name='admin_product_list'),
   
    path('admin-dashboard/products/add/', views.admin_product_add, name='admin_product_add'),
   
    path('admin-dashboard/products/edit/<int:product_id>/', views.admin_product_edit, name='admin_product_edit'),
   
    path('admin-dashboard/products/delete/<int:product_id>/', views.admin_product_delete, name='admin_product_delete'),
  
    path('admin-dashboard/categories/', views.admin_category_list, name='admin_category_list'),
   
    path('admin-dashboard/categories/add/', views.admin_category_add, name='admin_category_add'),
  
    path('admin-dashboard/categories/edit/<int:category_id>/', views.admin_category_edit, name='admin_category_edit'),
   
    path('admin-dashboard/categories/delete/<int:category_id>/', views.admin_category_delete, name='admin_category_delete'),
   
    path('admin-dashboard/orders/', views.admin_all_orders, name='admin_all_orders'),
  
    path('admin-dashboard/users/', views.admin_user_list, name='admin_user_list'),
  
    path('profile/', views.profile_edit, name='profile_edit'),
  
    path('admin-dashboard/profile/', views.admin_profile, name='admin_profile'),
  
    path('admin-dashboard/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
   
    path('admin-dashboard/orders/export/', views.export_orders_csv, name='export_orders_csv'),
  
    path('admin-dashboard/users/export/', views.export_users_csv, name='export_users_csv'),
   
    path('contact-us/', views.contact_us, name='contact_us'),
   
    path('admin-dashboard/messages/', views.admin_contact_messages, name='admin_contact_messages'),
   
    path('mark-message-read/<int:message_id>/', views.mark_message_read, name='mark_message_read'),
]