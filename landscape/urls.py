from django.urls import path
from . import views

urlpatterns = [
    # Landscape list views
    path('landscape/',           views.bidPipeline,       name='bid_pipeline'),
    path('landscape/projects/',  views.activeProjects,    name='active_projects'),
    path('landscape/completed/', views.completedProjects, name='completed_projects'),

    # Bid CRUD
    path('landscape/create_bid/',              views.createBid,  name='create_bid'),
    path('landscape/bid/<uuid:uuid>/',         views.viewBid,    name='view_bid'),
    path('landscape/update_bid/<uuid:uuid>/',  views.updateBid,  name='update_bid'),
    path('landscape/delete_bid/<uuid:uuid>/',  views.deleteBid,  name='delete_bid'),

    # Change Order CRUD
    path('landscape/bid/<uuid:uuid>/add_co/',  views.addChangeOrder,    name='add_co'),
    path('landscape/co/<uuid:uuid>/',          views.viewChangeOrder,   name='view_co'),
    path('landscape/co/<uuid:uuid>/update/',   views.updateChangeOrder, name='update_co'),
    path('landscape/co/<uuid:uuid>/delete/',   views.deleteChangeOrder, name='delete_co'),

    # Daily Log
    path('landscape/bid/<uuid:uuid>/add_log/', views.addLogEntry,    name='add_log'),
    path('landscape/log/<uuid:uuid>/update/',  views.updateLogEntry, name='update_log'),
    path('landscape/log/<uuid:uuid>/delete/',  views.deleteLogEntry, name='delete_log'),
]
