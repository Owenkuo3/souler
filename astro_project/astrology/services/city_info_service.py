
def get_city_coordinates(city_name):
    from users.models import City
    city = City.objects.filter(name=city_name).first()
    if city:
        return city.latitude, city.longitude
    return None, None
