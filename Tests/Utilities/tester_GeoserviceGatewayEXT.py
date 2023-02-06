from pprint import pprint

model_profile = {
    "age": 0,
    "careerField": "Aviation Professional",
    "community": "Gujarati",
    "countryRaisedIn": "United Kingdom",
    "dateOfBirth": "2021-12-25 13:33:44.426700+00:00",
    "description": "Testing Description",
    "doYouDrink": "Sometimes",
    "doYouSmoke": "Never",
    "doYouWantBabies": "Yes",
    "doYouWorkOut": "Everyday",
    "education": "Professional Degree",
    "email": "JasonKalkanus@gmail.com",
    "firstName": "Jason",
    "genderIdentity": "Male",
    "geohash": "75cm8wx9pwuu",
    "geohash1": "7",
    "geohash2": "75",
    "geohash3": "75c",
    "geohash4": "75cm",
    "geohash5": "75cm8",
    "headline": "Kshitiz Sharma. ",
    "height": 193.04000000000002,
    "id": "2LC0auvwmdEBtJZAdFau3JrdmRHI",
    "image1": {
        "firebaseImagePath": "images/QvV4OoZmZ3QWHhMNaZrr7lkqmLF3/image1640439314.5542731.heic",
        "imageURL": "https://firebasestorage.googleapis.com/v0/b/amore-f8cd6.appspot.com/o/images%2FQvV4OoZmZ3QWHhMNaZrr7lkqmLF3%2Fimage1640439314.5542731.heic?alt=media&token=cb324857-1cf9-4ee1-b208-ddba11751275"
    },
    "image2": {
        "firebaseImagePath": "images/QvV4OoZmZ3QWHhMNaZrr7lkqmLF3/image1640439322.9451962.heic",
        "imageURL": "https://firebasestorage.googleapis.com/v0/b/amore-f8cd6.appspot.com/o/images%2FQvV4OoZmZ3QWHhMNaZrr7lkqmLF3%2Fimage1640439322.9451962.heic?alt=media&token=9db4870e-4d0d-4c91-b2ed-5e73b7a38512"
    },
    "image3": {
        "firebaseImagePath": "images/QvV4OoZmZ3QWHhMNaZrr7lkqmLF3/image1640459447.988801.heic",
        "imageURL": "https://firebasestorage.googleapis.com/v0/b/amore-f8cd6.appspot.com/o/images%2FQvV4OoZmZ3QWHhMNaZrr7lkqmLF3%2Fimage1640459447.988801.heic?alt=media&token=dff3b772-5a59-4cf9-91e1-5f82757575dd"
    },
    "image4": {
        "firebaseImagePath": "images/QvV4OoZmZ3QWHhMNaZrr7lkqmLF3/image1640459453.9551349.heic",
        "imageURL": "https://firebasestorage.googleapis.com/v0/b/amore-f8cd6.appspot.com/o/images%2FQvV4OoZmZ3QWHhMNaZrr7lkqmLF3%2Fimage1640459453.9551349.heic?alt=media&token=7bfe0149-476b-49fa-b141-8165e2c8a063"
    },
    "image5": {
        "firebaseImagePath": "images/QvV4OoZmZ3QWHhMNaZrr7lkqmLF3/image1640459486.062407.heic",
        "imageURL": "https://firebasestorage.googleapis.com/v0/b/amore-f8cd6.appspot.com/o/images%2FQvV4OoZmZ3QWHhMNaZrr7lkqmLF3%2Fimage1640459486.062407.heic?alt=media&token=efd58043-a7ad-4564-be1d-559127cfa93d"
    },
    "image6": {},
    "interests": [
        "Shopping",
        "Art"
    ],
    "jobTitle": "VP",
    "lastName": "Kalkanus",
    "location": {
        "latitude": -22.903539,
        "longitude": -43.2095869
    },
    "notificationsStatus": False,
    "profileCompletion": 89.13,
    "profileDistanceFromUser": 0.0,
    "religion": "Spiritual",
    "school": "Stevens Institute of Tech ",
    "sexualOrientation": [
        "Straight",
        "Bisexual"
    ],
    "sexualOrientationVisible": False,
    "showMePreference": "Women",
    "wasProfileUpdated": True,
    "work": "Nasdaq"
}

# model_profile_encoded = Profile.encode_data_for_redis(model_profile)
# pprint(model_profile_encoded)
# print(len(list(model_profile_encoded.keys())))

# redis_result = {'id': 'profile:mLrI67GOQ8nSbosUmftd', 'doYouWorkOut': 'Everyday', 'firstName': 'Jason', 'school': 'Stevens Institute of Tech ', 'geohash3': '75c', 'geohash1': '7', 'isProfileActive': 'true', 'genderIdentity': 'Male', 'image5': '{"firebaseImagePath": "images/QvV4OoZmZ3QWHhMNaZrr7lkqmLF3/image1640459486.062407.heic", "imageURL": "https://firebasestorage.googleapis.com/v0/b/amore-f8cd6.appspot.com/o/images%2FQvV4OoZmZ3QWHhMNaZrr7lkqmLF3%2Fimage1640459486.062407.heic?alt=media&token=efd58043-a7ad-4564-be1d-559127cfa93d"}', 'email': 'JasonKalkanus@gmail.com', 'description': 'Testing Description', 'careerField': 'Aviation Professional', 'sexualOrientation': '["Straight", "Bisexual"]', 'doYouDrink': 'Sometimes', 'education': 'Professional Degree', 'jobTitle': 'VP', 'location': {'latitude': -22.903539, 'longitude': -43.2095869}, 'doYouWantBabies': 'Yes', 'dateOfBirth': '2021-12-25 13:33:44.426700+00:00', 'showMePreference': 'Women', 'religion': 'Spiritual', 'geohash4': '75cm', 'geohash2': '75', 'geohash5': '75cm8', 'profileCompletion': '89.13', 'height': '193.04000000000002', 'image2': '{"firebaseImagePath": "images/QvV4OoZmZ3QWHhMNaZrr7lkqmLF3/image1640439322.9451962.heic", "imageURL": "https://firebasestorage.googleapis.com/v0/b/amore-f8cd6.appspot.com/o/images%2FQvV4OoZmZ3QWHhMNaZrr7lkqmLF3%2Fimage1640439322.9451962.heic?alt=media&token=9db4870e-4d0d-4c91-b2ed-5e73b7a38512"}', 'community': 'Gujarati', 'geohash': '75cm8wx9pwuu', 'wasProfileUpdated': 'true', 'headline': 'Kshitiz Sharma. ', 'doYouSmoke': 'Never', 'lastName': 'Kalkanus', 'image3': '{"firebaseImagePath": "images/QvV4OoZmZ3QWHhMNaZrr7lkqmLF3/image1640459447.988801.heic", "imageURL": "https://firebasestorage.googleapis.com/v0/b/amore-f8cd6.appspot.com/o/images%2FQvV4OoZmZ3QWHhMNaZrr7lkqmLF3%2Fimage1640459447.988801.heic?alt=media&token=dff3b772-5a59-4cf9-91e1-5f82757575dd"}', 'countryRaisedIn': 'United Kingdom', 'image1': '{"firebaseImagePath": "images/QvV4OoZmZ3QWHhMNaZrr7lkqmLF3/image1640439314.5542731.heic", "imageURL": "https://firebasestorage.googleapis.com/v0/b/amore-f8cd6.appspot.com/o/images%2FQvV4OoZmZ3QWHhMNaZrr7lkqmLF3%2Fimage1640439314.5542731.heic?alt=media&token=cb324857-1cf9-4ee1-b208-ddba11751275"}', 'interests': '["Shopping", "Art"]', 'work': 'Nasdaq', 'image4': '{"firebaseImagePath": "images/QvV4OoZmZ3QWHhMNaZrr7lkqmLF3/image1640459453.9551349.heic", "imageURL": "https://firebasestorage.googleapis.com/v0/b/amore-f8cd6.appspot.com/o/images%2FQvV4OoZmZ3QWHhMNaZrr7lkqmLF3%2Fimage1640459453.9551349.heic?alt=media&token=7bfe0149-476b-49fa-b141-8165e2c8a063"}'}
# model_profile_decoded = Profile.decode_data_from_redis(redis_result)
# decoded_dict = asdict(model_profile_decoded, dict_factory=ignore_none)
# pprint(decoded_dict)
# print(len(list(decoded_dict.keys())))

# for _ in range(100):
#     redis_client.hset(f"profile:{model_profile['id']}", mapping=model_profile_encoded)