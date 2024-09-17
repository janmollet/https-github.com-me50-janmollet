from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
import pyautogui
from django.contrib import messages

from .models import User, Listing, Category, Watch, Bid, Comments


def index(request):
    # Obtener todos los listados activos, ordenados por fecha de creación descendente
    active_listings = Listing.objects.filter(is_active=True).order_by('-created_at')

    # Iterar sobre cada listado activo para obtener la información requerida
    for listing in active_listings:
        # Obtener la oferta más alta (highest_bid) y el último postor (last_bidder)
        highest_bid = listing.highest_bid()
        last_bid = listing.bids.last()  # Obtener la última oferta
        
        # Asignar valores para mostrar en la plantilla
        listing.latest_bid = last_bid.amount if last_bid else " - "
        listing.last_bidder = last_bid.user if last_bid else "No bidder yet"

    # Pasar los listados activos con la información de la última oferta a la plantilla
    return render(request, 'auctions/index.html', {'active_listings': active_listings})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def listing(request):
    return render(request, "auctions/listing.html")


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
    
def listing(request):
    if request.method == "GET":
        allCategories = Category.objects.all()
        return render(request, "auctions/listing.html", {"categories": allCategories})
    elif request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        starting_bid = request.POST.get("bid")
        image = request.POST.get("imagen")
        category_name = request.POST.get("category_name")
        currentUser = request.user
        
        if not category_name:
            return render(request, "auctions/listing.html", {"error": "Please select a category."})

        # Fetch or create a Category instance based on the provided category name
        category_instance, _ = Category.objects.get_or_create(category_name=category_name)

        # Create a new listing object and save it to the database
        new_listing = Listing.objects.create(
            title=title, 
            description=description, 
            starting_bid=starting_bid, 
            image=image, 
            category=category_instance, 
            owner=currentUser
        )

        latest_bid = Bid.objects.filter(listing=new_listing).order_by('amount').first()

        # Pass the new_listing and latest_bid to the template for rendering
        return render(request, "auctions/listing_detail.html", {
            "listing": new_listing,
            "latest_bid": latest_bid,
        })

        # Redirigir al usuario a la página de detalles del nuevo listado
        return HttpResponseRedirect(reverse("index"))
    else:
        # Si el método de solicitud no es GET ni POST, redirigir a la página de inicio
        return HttpResponseRedirect(reverse("index"))
def listing_detail(request, listing_id):
    # Obtener el objeto de listado correspondiente al ID proporcionado
    listing = Listing.objects.get(pk=listing_id)
    comments = listing.comments.all()
    if request.method == 'POST':
        comment_text = request.POST.get('comment_text')
        user = request.user

        # Create a new comment object
        comment = Comments.objects.create(user=user, listing=listing, comentari=comment_text)

        # Optionally, you might want to add validation or error handling here

        # Redirect back to the same page to refresh comments
        return redirect('listing_detail', listing_id=listing_id)

    context = {
        'listing': listing,
        'comments': comments,
    }
    return render(request, 'auctions/listing_detail.html', context)

def categories(request):
    # Recupera todas las categorías
    categories = Category.objects.all()

    # Recupera todos los listados
    listings = Listing.objects.all()

    # Crea un diccionario para almacenar listados por categoría
    category_listings = {}
    for category in categories:
        # Filtra los listados por categoría y los almacena en el diccionario
        category_listings[category] = listings.filter(category=category)

    return render(request, 'auctions/categories.html', {'category_listings': category_listings})


def save_to_watchlist(request, listing_id):
    if request.method == 'POST':
        listing = get_object_or_404(Listing, pk=listing_id)
        user = request.user
        
        # Check if the user is the owner of the listing
        if user == listing.owner:
            pyautogui.alert(request, "No puedes añadir tu propio producto a tu lista de seguimiento.")
            return redirect('index')
        
        # Check if the listing is already in the user's watchlist
        if Watch.objects.filter(user=user, listing=listing).exists():
            pyautogui.alert(request, "Este producto ya está en tu lista de seguimiento.")
        else:
            Watch.objects.create(user=user, listing=listing)
            pyautogui.alert(request, "Producto añadido a tu lista de seguimiento.")
            return redirect('watchlist')
        
        # Retrieve the latest bid associated with the listing
        latest_bid = Bid.objects.filter(listing=listing).order_by('amount').first()
        
        # Render the listing detail view with latest_bid information
        return render(request, 'auctions/watchlist.html', {
            'listing': listing,
            'latest_bid': latest_bid,
        })
    
    else:
        return redirect('watchlist')

def watchlist(request):
    if request.user.is_authenticated:
        # Obtener todas las entradas de la watchlist para el usuario actual
        watchlist_entries = Watch.objects.filter(user=request.user)

        # Iterar sobre cada entrada y actualizar latest_bid y last_bidder si es necesario
        for entry in watchlist_entries:
            # Obtener el último bid para el listado asociado a esta entrada de watchlist
            latest_bid = Bid.objects.filter(listing=entry.listing).order_by('-amount').first()
            
            # Actualizar latest_bid en la entrada de watchlist
            if latest_bid:
                entry.latest_bid = latest_bid.amount
                entry.last_bidder = latest_bid.user.username
            else:
                entry.latest_bid = entry.listing.starting_bid  # Usar starting_bid si no hay bids
                entry.last_bidder = None  # No hay postor si no hay bids

        return render(request, 'auctions/watchlist.html', {'watchlist_entries': watchlist_entries})
    else:
        return redirect('login')

def remove_from_watchlist(request, listing_id):
    watch_entry = get_object_or_404(Watch, listing_id=listing_id, user=request.user)
    
    if request.method == 'POST':
        watch_entry.delete()
    
    
    return redirect('watchlist')

def place_bid(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    
    if request.method == 'POST':
        amount = request.POST.get('bid')
        
        # Validate the bid amount
        try:
            amount = float(amount)
        except ValueError:
            pyautogui.alert(request, 'Invalid bid amount. Please enter a valid number.')
            return redirect('listing_detail', listing_id=listing.id)
        
        if amount < listing.starting_bid:
            pyautogui.alert(request, 'Bid must be at least the same as the starting bid.')
            return redirect('listing_detail', listing_id=listing.id)
        
        highest_bid = listing.highest_bid()
        if highest_bid is not None and amount <= highest_bid:
            pyautogui.alert(request, 'Bid must be higher than the current highest bid.')
            return redirect('listing_detail', listing_id=listing.id)
        
        # Create a new Bid object and save it
        bid = Bid(listing=listing, user=request.user, amount=amount)
        bid.save()
        
        pyautogui.alert(request, 'Your bid has been placed successfully.')
        return redirect('listing_detail', listing_id=listing.id)
    
    return redirect('index', listing_id=listing.id)

def close_auction(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    if listing.is_active:
        highest_bid = listing.highest_bid()
        if highest_bid > listing.starting_bid:
            winning_bids = Bid.objects.filter(listing=listing, amount=highest_bid)
            if winning_bids.exists():
                watch_entries = Watch.objects.filter(listing=listing)
                for entry in watch_entries:
                    if entry.user in [bid.user for bid in winning_bids]:
                        entry.has_won = True
                        entry.save()

                listing.is_active = False
                listing.save()
                # Obtén el primer usuario ganador
                winner = winning_bids.first().user
                # Renderiza la plantilla 'close.html' con el contexto del ganador
                return render(request, 'auctions/close.html', {'winner': winner})
    
    # Si no se cumplen las condiciones anteriores, redirige a algún lugar apropiado
    return redirect('index')

def comentario(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    if request.method == 'POST':
        comment_text = request.POST.get('comment_text')
        user = request.user

        # Create a new comment object
        comment = Comments.objects.create(user=user, listing=listing, comentari=comment_text)

        # Optionally, you might want to add validation or error handling here

        # Add a success message
        messages.success(request, 'Your comment has been added successfully.')

        # Redirect back to the listing detail page
        return redirect('listing_detail', listing_id=listing_id)

    # If it's a GET request or any other case, render the listing detail template
    context = {
        'listing': listing,
    }
    return render(request, 'auctions/listing_detail.html', context)
