"""
Management command to create default point types with multilingual names.

Usage: python manage.py create_default_types
"""
import os
import shutil
import uuid as uuid_lib
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from yaml import serialize
from apps.points.models import PointType

from ...serializers import PointTypeSerializer


class Command(BaseCommand):
    help = 'Create default point types (base types with multilingual support)'

    def load_icon(self, icon_value):
        """
        Load icon - either return emoji as-is or copy image file to media storage.

        If icon_value ends with .png, .jpg, .jpeg, .gif, .svg, it's treated as a file path
        relative to the base_types_icons directory. The file is copied to media/point_type_icons/
        with a unique base-prefixed filename to avoid conflicts with user uploads.

        Returns the icon value (emoji or media URL for images).
        """
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')

        if icon_value.lower().endswith(image_extensions):
            # This is an image file reference
            icons_dir = Path(__file__).parent / 'base_types_icons'
            icon_path = icons_dir / icon_value

            if not icon_path.exists():
                self.stdout.write(
                    self.style.WARNING(f'Image file not found: {icon_path}. Using placeholder.')
                )
                return '📍'  # Default placeholder

            try:
                # Generate unique filename with 'base_' prefix to distinguish from user uploads
                # Keep original filename for readability
                file_ext = icon_path.suffix
                base_filename = icon_path.stem
                unique_filename = f"base_{base_filename}_{uuid_lib.uuid4().hex[:8]}{file_ext}"
                media_path = os.path.join('point_type_icons', unique_filename)

                # Check if file already exists in media storage
                if default_storage.exists(media_path):
                    # File already exists, build and return absolute URL
                    base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                    media_url = settings.MEDIA_URL.lstrip('/')
                    return f"{base_url}/{media_url}{media_path}"

                # Read the image file
                with open(icon_path, 'rb') as img_file:
                    file_content = img_file.read()

                # Save to media storage
                saved_path = default_storage.save(media_path, ContentFile(file_content))

                # Build absolute URL (like the upload API does)
                # Get base URL from settings or use default
                base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                media_url = settings.MEDIA_URL.lstrip('/')
                icon_url = f"{base_url}/{media_url}{saved_path}"

                self.stdout.write(
                    self.style.SUCCESS(f'  → Copied icon: {icon_value} → {icon_url}')
                )
                return icon_url

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error loading image {icon_path}: {e}')
                )
                return '📍'  # Default placeholder on error

        # It's an emoji, return as-is
        return icon_value

    def handle(self, *args, **options):
        """Create default point types with English and French translations."""
        # === DEFAULT GENERIC POINT ===
        PointType.get_default_type()  # Create default 'Point' type

        default_types = [
            # === NATURE & LANDSCAPE (1-15) ===
            {'names': {'en': 'Viewing Point', 'fr': 'Point de vue'}, 'icon': 'viewpoint.png', 'order': 1},
            {'names': {'en': 'Summit', 'fr': 'Sommet'}, 'icon': '⛰️', 'order': 2},
            {'names': {'en': 'Mountain Pass', 'fr': 'Col'}, 'icon': '🏔️', 'order': 3},
            {'names': {'en': 'Water Point', 'fr': "Point d'eau"}, 'icon': '💧', 'order': 4},
            {'names': {'en': 'Waterfall', 'fr': 'Cascade'}, 'icon': 'waterfall.png', 'order': 5},
            {'names': {'en': 'Forest', 'fr': 'Forêt'}, 'icon': 'forest.png', 'order': 6},
            {'names': {'en': 'Desert', 'fr': 'Désert'}, 'icon': '🏜️', 'order': 7},
            {'names': {'en': 'Mushroom', 'fr': 'Champignon'}, 'icon': '🍄‍🟫', 'order': 8},
            {'names': {'en': 'Swimming Area', 'fr': 'Zone de baignade'}, 'icon': '🏊', 'order': 9},
            {'names': {'en': 'Lake', 'fr': 'Lac'}, 'icon': '🏞️', 'order': 10},
            {'names': {'en': 'River', 'fr': 'Rivière'}, 'icon': '🏞️', 'order': 11},
            {'names': {'en': 'Cave', 'fr': 'Grotte'}, 'icon': '🕳️', 'order': 12},
            {'names': {'en': 'Beach', 'fr': 'Plage'}, 'icon': '🏖️', 'order': 13},
            {'names': {'en': 'Park', 'fr': 'Parc'}, 'icon': '🌳', 'order': 14},
            {'names': {'en': 'Garden', 'fr': 'Jardin'}, 'icon': '🌺', 'order': 15},

            # === ACCOMMODATION & FOOD (16-25) ===
            {'names': {'en': 'Restaurant', 'fr': 'Restaurant'}, 'icon': '🍽️', 'order': 16},
            {'names': {'en': 'Hotel', 'fr': 'Hôtel'}, 'icon': '🏨', 'order': 17},
            {'names': {'en': 'Campsite', 'fr': 'Camping'}, 'icon': '⛺', 'order': 18},
            {'names': {'en': 'Shelter', 'fr': 'Refuge'}, 'icon': '🏠', 'order': 19},
            {'names': {'en': 'Food', 'fr': 'Nourriture'}, 'icon': 'food.png', 'order': 20},
            {'names': {'en': 'Burger', 'fr': 'Burger'}, 'icon': '🍔', 'order': 21},
            {'names': {'en': 'Salad', 'fr': 'Salade'}, 'icon': '🥗', 'order': 22},
            {'names': {'en': 'Drink', 'fr': 'Boisson'}, 'icon': '🥤', 'order': 23},
            {'names': {'en': 'Bar', 'fr': 'Bar'}, 'icon': '🍺', 'order': 24},
            {'names': {'en': 'Cafe', 'fr': 'Café'}, 'icon': '☕', 'order': 25},

            # === NAVIGATION & WAYPOINTS (26-35) ===
            {'names': {'en': 'Finish Line', 'fr': "Ligne d'arrivée"}, 'icon': '🏁', 'order': 26},
            {'names': {'en': 'Start Line', 'fr': 'Ligne de départ'}, 'icon': '🚩', 'order': 27},
            {'names': {'en': 'Entrance', 'fr': 'Entrée'}, 'icon': 'entry.png', 'order': 28},
            {'names': {'en': 'Exit', 'fr': 'Sortie'}, 'icon': 'exit.png', 'order': 29},
            {'names': {'en': 'Parking', 'fr': 'Parking'}, 'icon': '🅿️', 'order': 30},
            {'names': {'en': 'Tunnel', 'fr': 'Tunnel'}, 'icon': 'tunnel.png', 'order': 31},
            {'names': {'en': 'Bridge', 'fr': 'Pont'}, 'icon': 'bridge.png', 'order': 32},
            {'names': {'en': 'Crossroads', 'fr': 'Carrefour'}, 'icon': 'crossroad.png', 'order': 33},
            {'names': {'en': 'Border', 'fr': 'Frontière'}, 'icon': 'border.png', 'order': 34},
            {'names': {'en': 'Landmark', 'fr': 'Point de repère'}, 'icon': 'landmark.png', 'order': 35},

            # === SAFETY & HAZARDS (36-45) ===
            {'names': {'en': 'Dangerous Area', 'fr': 'Zone dangereuse'}, 'icon': 'danger.png', 'order': 36},
            {'names': {'en': 'Mine', 'fr': 'Mine'}, 'icon': 'mine.png', 'order': 37},
            {'names': {'en': 'Hunting Area', 'fr': 'Zone de chasse'}, 'icon': 'hunting_area.png', 'order': 38},
            {'names': {'en': 'Drop Zone', 'fr': 'Zone de parachutage'}, 'icon': '🪂', 'order': 39},
            {'names': {'en': 'Alarm', 'fr': 'Alarme'}, 'icon': 'alarm.png', 'order': 40},
            {'names': {'en': 'Police', 'fr': 'Police'}, 'icon': '👮', 'order': 41},
            {'names': {'en': 'Fire Station', 'fr': 'Pompier'}, 'icon': '🚒', 'order': 42},
            {'names': {'en': 'Hospital', 'fr': 'Hôpital'}, 'icon': '🏥', 'order': 43},
            {'names': {'en': 'First Aid', 'fr': 'Premiers secours'}, 'icon': 'first-aid.png', 'order': 44},
            {'names': {'en': 'Danger Sign', 'fr': 'Panneau de danger'}, 'icon': '⚠️', 'order': 45},

            # === TRANSPORTATION (46-65) ===
            {'names': {'en': 'Aerodrome', 'fr': 'Aérodrome'}, 'icon': '✈️', 'order': 46},
            {'names': {'en': 'Bicycle', 'fr': 'Vélo'}, 'icon': '🚲', 'order': 47},
            {'names': {'en': 'Motorcycle', 'fr': 'Moto'}, 'icon': '🏍️', 'order': 48},
            {'names': {'en': 'Bus', 'fr': 'Bus'}, 'icon': '🚌', 'order': 49},
            {'names': {'en': 'Train', 'fr': 'Train'}, 'icon': '🚂', 'order': 50},
            {'names': {'en': 'Plane', 'fr': 'Avion'}, 'icon': '✈️', 'order': 51},
            {'names': {'en': 'Car', 'fr': 'Voiture'}, 'icon': '🚗', 'order': 52},
            {'names': {'en': 'Truck', 'fr': 'Camion'}, 'icon': '🚚', 'order': 53},
            {'names': {'en': 'Tram', 'fr': 'Tramway'}, 'icon': '🚋', 'order': 54},
            {'names': {'en': 'Horse', 'fr': 'Cheval'}, 'icon': '🐴', 'order': 55},
            {'names': {'en': 'Boat', 'fr': 'Bateau'}, 'icon': '⛵', 'order': 56},
            {'names': {'en': 'Hot Air Balloon', 'fr': 'Montgolfière'}, 'icon': 'hot-air-balloon.png', 'order': 57},
            {'names': {'en': 'Bus Stop', 'fr': 'Arrêt de bus'}, 'icon': '🚏', 'order': 58},
            {'names': {'en': 'Train Station', 'fr': 'Gare'}, 'icon': '🚉', 'order': 59},
            {'names': {'en': 'Airport', 'fr': 'Aéroport'}, 'icon': '🛫', 'order': 60},
            {'names': {'en': 'Heliport', 'fr': 'Héliport'}, 'icon': '🚁', 'order': 61},
            {'names': {'en': 'Taxi', 'fr': 'Taxi'}, 'icon': '🚕', 'order': 62},
            {'names': {'en': 'Rental Car', 'fr': 'Location de voiture'}, 'icon': '🚙', 'order': 63},
            {'names': {'en': 'Gas Station', 'fr': 'Station-service'}, 'icon': '⛽', 'order': 64},
            {'names': {'en': 'Garage', 'fr': 'Garage'}, 'icon': '🔧', 'order': 65},

            # === BUILDINGS & STRUCTURES (66-80) ===
            {'names': {'en': 'House', 'fr': 'Maison'}, 'icon': '🏠', 'order': 66},
            {'names': {'en': 'Castle', 'fr': 'Château'}, 'icon': '🏰', 'order': 67},
            {'names': {'en': 'Monument', 'fr': 'Monument'}, 'icon': '🗿', 'order': 68},
            {'names': {'en': 'Lighthouse', 'fr': 'Phare'}, 'icon': 'lighthouse.png', 'order': 69},
            {'names': {'en': 'Wall', 'fr': 'Mur'}, 'icon': '🧱', 'order': 70},
            {'names': {'en': 'Antenna', 'fr': 'Antenne'}, 'icon': '📡', 'order': 71},
            {'names': {'en': 'Bell', 'fr': 'Cloche'}, 'icon': '🔔', 'order': 72},
            {'names': {'en': 'Tower', 'fr': 'Tour'}, 'icon': '🗼', 'order': 73},
            {'names': {'en': 'Fortress', 'fr': 'Forteresse'}, 'icon': '🏯', 'order': 74},
            {'names': {'en': 'Ruins', 'fr': 'Ruines'}, 'icon': '🏛️', 'order': 75},
            {'names': {'en': 'Windmill', 'fr': 'Moulin'}, 'icon': 'windmill.png', 'order': 76},
            {'names': {'en': 'Factory', 'fr': 'Usine'}, 'icon': '🏭', 'order': 77},
            {'names': {'en': 'Stadium', 'fr': 'Stade'}, 'icon': '🏟️', 'order': 78},
            {'names': {'en': 'Circus', 'fr': 'Cirque'}, 'icon': '🎪', 'order': 79},
            {'names': {'en': 'Fountain', 'fr': 'Fontaine'}, 'icon': '⛲', 'order': 80},

            # === RELIGIOUS BUILDINGS (81-85) ===
            {'names': {'en': 'Church', 'fr': 'Église'}, 'icon': '⛪', 'order': 81},
            {'names': {'en': 'Temple', 'fr': 'Temple'}, 'icon': '🛕', 'order': 82},
            {'names': {'en': 'Synagogue', 'fr': 'Synagogue'}, 'icon': '🕍', 'order': 83},
            {'names': {'en': 'Mosque', 'fr': 'Mosquée'}, 'icon': '🕌', 'order': 84},
            {'names': {'en': 'Chapel', 'fr': 'Chapelle'}, 'icon': '⛪', 'order': 85},

            # === CULTURAL & HISTORICAL (86-95) ===
            {'names': {'en': 'Archaeological Site', 'fr': 'Site archéologique'}, 'icon': '🏛️', 'order': 86},
            {'names': {'en': 'Museum', 'fr': 'Musée'}, 'icon': '🏛️', 'order': 87},
            {'names': {'en': 'Library', 'fr': 'Bibliothèque'}, 'icon': '📚', 'order': 88},
            {'names': {'en': 'Music', 'fr': 'Musique'}, 'icon': '🎵', 'order': 89},
            {'names': {'en': 'Theater', 'fr': 'Théâtre'}, 'icon': '🎭', 'order': 90},
            {'names': {'en': 'Cinema', 'fr': 'Cinéma'}, 'icon': '🎬', 'order': 91},
            {'names': {'en': 'Gallery', 'fr': 'Galerie'}, 'icon': '🖼️', 'order': 92},
            {'names': {'en': 'Memorial', 'fr': 'Mémorial'}, 'icon': '🕯️', 'order': 93},
            {'names': {'en': 'Statue', 'fr': 'Statue'}, 'icon': '🗽', 'order': 94},
            {'names': {'en': 'Historical Site', 'fr': 'Site historique'}, 'icon': '📜', 'order': 95},

            # === SERVICES (96-110) ===
            {'names': {'en': 'Information', 'fr': 'Information'}, 'icon': 'ℹ️', 'order': 96},
            {'names': {'en': 'ATM', 'fr': 'ATM'}, 'icon': 'atm.png', 'order': 97},
            {'names': {'en': 'Telephone', 'fr': 'Téléphone'}, 'icon': '☎️', 'order': 98},
            {'names': {'en': 'Post Office', 'fr': 'Poste'}, 'icon': '📮', 'order': 99},
            {'names': {'en': 'Laundry', 'fr': 'Laverie'}, 'icon': '🧺', 'order': 100},
            {'names': {'en': 'Shower', 'fr': 'Douche'}, 'icon': '🚿', 'order': 101},
            {'names': {'en': 'Toilet', 'fr': 'Toilettes'}, 'icon': '🚻', 'order': 102},
            {'names': {'en': 'Market', 'fr': 'Marché'}, 'icon': '🏪', 'order': 103},
            {'names': {'en': 'Shop', 'fr': 'Magasin'}, 'icon': '🏬', 'order': 104},
            {'names': {'en': 'Supermarket', 'fr': 'Supermarché'}, 'icon': '🛒', 'order': 105},
            {'names': {'en': 'Bank', 'fr': 'Banque'}, 'icon': '🏦', 'order': 106},
            {'names': {'en': 'Pharmacy', 'fr': 'Pharmacie'}, 'icon': 'pharmacy.png', 'order': 107},
            {'names': {'en': 'Bakery', 'fr': 'Boulangerie'}, 'icon': '🥖', 'order': 108},
            {'names': {'en': 'Butcher', 'fr': 'Boucherie'}, 'icon': '🥩', 'order': 109},
            {'names': {'en': 'Accessible', 'fr': 'Handicapé'}, 'icon': 'accessible.png', 'order': 110},

            # === ACTIVITIES & RECREATION (111-120) ===
            {'names': {'en': 'Picnic Area', 'fr': 'Zone de picnic'}, 'icon': '🧺', 'order': 111},
            {'names': {'en': 'Playground', 'fr': 'Aire de jeux'}, 'icon': '🎠', 'order': 112},
            {'names': {'en': 'Sports Field', 'fr': 'Terrain de sport'}, 'icon': '⚽', 'order': 113},
            {'names': {'en': 'Target', 'fr': 'Cible'}, 'icon': '🎯', 'order': 114},
            {'names': {'en': 'Fishing', 'fr': 'Pêche'}, 'icon': '🎣', 'order': 115},
            {'names': {'en': 'Climbing', 'fr': 'Escalade'}, 'icon': '🧗', 'order': 116},
            {'names': {'en': 'Skiing', 'fr': 'Ski'}, 'icon': '⛷️', 'order': 117},
            {'names': {'en': 'Golf', 'fr': 'Golf'}, 'icon': '⛳', 'order': 118},
            {'names': {'en': 'Tennis', 'fr': 'Tennis'}, 'icon': '🎾', 'order': 119},
            {'names': {'en': 'Gym', 'fr': 'Salle de sport'}, 'icon': '🏋️', 'order': 120},

            # === PEOPLE & ANIMALS (121-130) ===
            {'names': {'en': 'Person', 'fr': 'Personne'}, 'icon': '🧑', 'order': 121},
            {'names': {'en': 'Dog', 'fr': 'Chien'}, 'icon': '🐕', 'order': 122},
            {'names': {'en': 'Bird', 'fr': 'Oiseau'}, 'icon': '🐦', 'order': 123},
            {'names': {'en': 'Wildlife', 'fr': 'Faune sauvage'}, 'icon': '🦌', 'order': 124},
            {'names': {'en': 'Cat', 'fr': 'Chat'}, 'icon': '🐈', 'order': 125},
            {'names': {'en': 'Cow', 'fr': 'Vache'}, 'icon': '🐄', 'order': 126},
            {'names': {'en': 'Sheep', 'fr': 'Mouton'}, 'icon': '🐑', 'order': 127},
            {'names': {'en': 'Farm', 'fr': 'Ferme'}, 'icon': '🚜', 'order': 128},
            {'names': {'en': 'Zoo', 'fr': 'Zoo'}, 'icon': '🦁', 'order': 129},
            {'names': {'en': 'Veterinarian', 'fr': 'Vétérinaire'}, 'icon': '🏥', 'order': 130},
        ]

        created_count = 0
        updated_count = 0

        for type_data in default_types:
            # Try to find existing type by English name
            english_name = type_data['names']['en']

            # Load the icon (emoji or image file)
            icon = self.load_icon(type_data['icon'])

            # Check if type already exists (by English name in names field)
            existing_types = PointType.objects.filter(
                owner=None,
                type_choice='base',
                names__has_key='en'
            )

            point_type = None
            for existing in existing_types:
                if existing.names.get('en') == english_name:
                    point_type = existing
                    break

            if point_type is None:
                # Create new base type
                point_type = PointType.objects.create(
                    names=type_data['names'],
                    creation_language='en',
                    type_choice='base',
                    owner=None,
                    visibility='public',
                    icon=icon,
                    order=type_data['order'],
                    status='active',
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created default type: {english_name} ({len(type_data["names"])} languages)'
                    )
                )
                created_count += 1
            else:
                # Update existing type with new translations if needed
                needs_update = False

                # Check if we need to add new translations
                for lang, name in type_data['names'].items():
                    if lang not in point_type.names or point_type.names[lang] != name:
                        point_type.names[lang] = name
                        needs_update = True

                # Check if icon needs updating
                if point_type.icon != icon:
                    point_type.icon = icon
                    needs_update = True

                # Check if type_choice needs updating
                if point_type.type_choice != 'base':
                    point_type.type_choice = 'base'
                    needs_update = True

                # Check if visibility needs updating
                if point_type.visibility != 'public':
                    point_type.visibility = 'public'
                    needs_update = True

                if needs_update:
                    point_type.save()
                    self.stdout.write(
                        self.style.WARNING(
                            f'Updated default type: {english_name} ({len(point_type.names)} languages)'
                        )
                    )
                    updated_count += 1
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Default type already up-to-date: {english_name}'
                        )
                    )

        # Summary
        self.stdout.write('\n' + '='*60)
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Created {created_count} new default type(s)'
                )
            )
        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Updated {updated_count} existing default type(s)'
                )
            )
        if created_count == 0 and updated_count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    '✓ All default types already exist and are up-to-date'
                )
            )
        self.stdout.write('='*60)
