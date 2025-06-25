# #!/usr/bin/env python3
# from models import db, Restaurant, RestaurantPizza, Pizza
# from flask_migrate import Migrate
# from flask import Flask, request, make_response, jsonify
# from flask_restful import Api, Resource
# import os

# BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

# app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# app.json.compact = False

# migrate = Migrate(app, db)

# db.init_app(app)

# api = Api(app)


# # @app.route("/")
# class Home(Resource):
#     def get(self):
#         return make_response("<h1>Code challenge</h1>")
# api.add_resource(Home, '/')

# class Restaurants(Resource):
#     def get(self):
        
#         restaurants=[restaurant.to_dict() for restaurant in Restaurant.query.all()]
#         return make_response(restaurants, 200)
#         # restaurants = []
#         # restaurant = Restaurant.query.all()
#         # for restaurant in restaurants.to_dict():
#         #     restaurants.append(restaurant)
#         #     return make_response(restaurants, 200)
        
    
# api.add_resource(Restaurants, '/restaurants')

# class RestaurantsId(Resource):
#     def get(self, id):
#         try:
#             restaurant = Restaurant.query.get(id)
#             return make_response(restaurant.to_dict(), 200)
#         except Exception as e:
#             return make_response({"Error": "Restaurant not found"}, 404)
 
#     def delete(self, id):
#         try:
#             restaurant = Restaurant.query.get(id)
#             db.session.delete(restaurant)
#             db.session.commit()
#             return make_response('Restaurant deleted successfully')
#         except Exception as e:
#             return make_response({"Error": "Restaurant not found"}, 404)
           
# api.add_resource(RestaurantsId, '/restaurants/<int:id>')

# class Pizzas(Resource):
#     def get(self):
#         pizzas=[pizza.to_dict() for pizza in Pizza.query.all()]
#         return make_response(jsonify(pizzas), 200)
    
#     def post(self): 
#         data = request.get_json()
        
#         # Basic validation
#         if not data or 'name' not in data or 'ingredients' not in data:
#             return make_response({'error': 'Name and ingredients are required.'}, 400)
        
#         try:
#             pizza = Pizza(name=data['name'], ingredients=data['ingredients'])
#             db.session.add(pizza)
#             db.session.commit()
#             return make_response(pizza.to_dict(), 201)
#         except Exception as e:
#             db.session.rollback()
#             return make_response({'error': str(e)}, 500)
           
# api.add_resource(Pizzas, '/pizza')




# if __name__ == "__main__":
#     app.run(port=5555, debug=True)




from models import db, Clinic, Patient, Insurance, Service, User, Booking, Review
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_restful import Api, Resource
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, verify_jwt_in_request
)
from functools import wraps
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL',
                                                       f'sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), "app.db")}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-jwt-secret')

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
api = Api(app)


# Role-based access decorator
def role_required(role):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            identity = get_jwt_identity()
            if identity.get('role') != role:
                return {'message': f'{role.capitalize()} role required!'}, 403
            return fn(*args, **kwargs)

        return decorator

    return wrapper


# Resource: User Registration
class UserRegistration(Resource):
    def post(self):
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return {'message': 'Username and password required'}, 400

        if User.query.filter_by(username=data['username']).first():
            return {'message': 'Username already exists'}, 400

        user = User(
            username=data['username'],
            role=data.get('role', 'patient')
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()

        return {'message': 'User created successfully'}, 201


# Resource: User Login
class UserLogin(Resource):
    def post(self):
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return {'message': 'Username and password required'}, 400

        user = User.query.filter_by(username=data['username']).first()
        if not user or not user.check_password(data['password']):
            return {'message': 'Invalid credentials'}, 401

        token = create_access_token(identity={
            'id': user.id,
            'username': user.username,
            'role': user.role
        })

        return {
            'access_token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        }, 200


# Resource: User Logout
class UserLogout(Resource):
    @jwt_required()
    def post(self):
        return {'message': 'Successfully logged out'}, 200


# Resource: Patient Dashboard
class PatientDashboard(Resource):
    @jwt_required()
    @role_required('patient')
    def get(self):
        current_user = get_jwt_identity()
        return {'message': f'Welcome Patient {current_user["username"]}'}, 200


# Resource: Clinic Dashboard
class ClinicDashboard(Resource):
    @jwt_required()
    @role_required('clinic')
    def get(self):
        current_user = get_jwt_identity()
        return {'message': f'Welcome Clinic Staff {current_user["username"]}'}, 200


# Resource: Admin Dashboard
class AdminDashboard(Resource):
    @jwt_required()
    @role_required('admin')
    def get(self):
        current_user = get_jwt_identity()
        return {'message': f'Welcome Admin {current_user["username"]}'}, 200


# Register API endpoints
api.add_resource(UserRegistration, '/api/register')
api.add_resource(UserLogin, '/api/login')
api.add_resource(UserLogout, '/api/logout')
api.add_resource(PatientDashboard, '/api/patient')
api.add_resource(ClinicDashboard, '/api/clinic')
api.add_resource(AdminDashboard, '/api/admin')

# Clinic routes
class Clinics(Resource):
    def get(self):
        try:
            clinics = [clinic.to_dict() for clinic in Clinic.query.all()]
            return clinics, 200
        except Exception as exc:
            return {'error': str(exc)}, 500

    def post(self):
        try:
            data = request.get_json()

            fields = ['id', 'name', 'specialty',
                               'contact', 'email', 'street', 'city']
            for field in fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400

            if Clinic.query.get(data['id']):
                return {'error': 'Clinic ID already exists'}, 400
            if Clinic.query.filter_by(contact=data['contact']).first():
                return {'error': 'Contact number already exists'}, 400
            if Clinic.query.filter_by(email=data['email']).first():
                return {'error': 'Email already exists'}, 400

            clinic = Clinic(
                id=data['id'],
                name=data['name'],
                specialty=data['specialty'],
                description=data.get('description'),
                contact=data['contact'],
                email=data['email'],
                street=data['street'],
                city=data['city'],
                image_url=data.get('image_url')
            )
            db.session.add(clinic)
            db.session.commit()
            return {'message': 'Clinic created successfully', 'clinic': clinic.to_dict()}, 201
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

class ClinicsById(Resource):
    def get(self, id):
        try:
            clinic = Clinic.query.get(id)
            if not clinic:
                return {'error': 'Clinic not found'}, 404
            return {'clinic': clinic.to_dict()}, 200
        except Exception as exc:
            return {'error': str(exc)}, 500

    def patch(self, id):
        try:
            clinic = Clinic.query.get(id)
            if not clinic:
                return {'error': 'Clinic not found'}, 404

            data = request.get_json()

            if 'contact' in data and data['contact'] != clinic.contact:
                if Clinic.query.filter_by(contact=data['contact']).first():
                    return {'error': 'Contact number already exists'}, 400

            if 'email' in data and data['email'] != clinic.email:
                if Clinic.query.filter_by(email=data['email']).first():
                    return {'error': 'Email already exists'}, 400

            fields = ['name', 'specialty', 'description',
                      'contact', 'email', 'street', 'city', 'image_url']
            for field in fields:
                if field in data:
                    setattr(clinic, field, data[field])

            db.session.commit()
            return {'message': 'Clinic updated successfully', 'clinic': clinic.to_dict()}, 200
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

    def delete(self, id):
        try:
            clinic = Clinic.query.get(id)
            if not clinic:
                return {'error': 'Clinic not found'}, 404

            db.session.delete(clinic)
            db.session.commit()
            return {'message': 'Clinic deleted successfully'}, 204
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

# Service routes
class Services(Resource):
    def get(self):
        try:
            services = [service.to_dict() for service in Service.query.all()]
            return services, 200
        except Exception as exc:
            return {'error': str(exc)}, 500

    def post(self):
        try:
            data = request.get_json()

            fields = ['name', 'price', 'duration']
            for field in fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400

            if Service.query.filter_by(name=data['name']).first():
                return {'error': 'Service name already exists'}, 400

            service = Service(
                name=data['name'],
                price=data['price'],
                duration=data['duration']
            )
            db.session.add(service)
            db.session.commit()
            return {'message': 'Service created successfully', 'service': service.to_dict()}, 201
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

class ServicesById(Resource):
    def get(self, id):
        try:
            service = Service.query.get(id)
            if not service:
                return {'error': 'Service not found'}, 404
            return {'service': service.to_dict()}, 200
        except Exception as exc:
            return {'error': str(exc)}, 500

    def patch(self, id):
        try:
            service = Service.query.get(id)
            if not service:
                return {'error': 'Service not found'}, 404

            data = request.get_json()

            if 'name' in data and data['name'] != service.name:
                if Service.query.filter_by(name=data['name']).first():
                    return {'error': 'Service name already exists'}, 400

            fields = ['name', 'price', 'duration']
            for field in fields:
                if field in data:
                    setattr(service, field, data[field])

            db.session.commit()
            return {'message': 'Service updated successfully', 'service': service.to_dict()}, 200
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

    def delete(self, id):
        try:
            service = Service.query.get(id)
            if not service:
                return {'error': 'Service not found'}, 404

            db.session.delete(service)
            db.session.commit()
            return {'message': 'Service deleted successfully'}, 204
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

# Insurance Routes
class Insurances(Resource):
    def get(self):
        try:
            insurances = [insurance.to_dict()
                          for insurance in Insurance.query.all()]
            return insurances, 200
        except Exception as exc:
            return {'error': str(exc)}, 500

    def post(self):
        try:
            data = request.get_json()

            if 'name' not in data:
                return {'error': 'Missing required field: name'}, 400

            if Insurance.query.filter_by(name=data['name']).first():
                return {'error': 'Insurance name already exists'}, 400

            insurance = Insurance(name=data['name'])

            db.session.add(insurance)
            db.session.commit()
            return {'message': 'Insurance created successfully', 'insurance': insurance.to_dict()}, 201
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

class InsurancesById(Resource):
    def get(self, id):
        try:
            insurance = Insurance.query.get(id)
            if not insurance:
                return {'error': 'Insurance not found'}, 404
            return {'insurance': insurance.to_dict()}, 200
        except Exception as exc:
            return {'error': str(exc)}, 500

    def patch(self, id):
        try:
            insurance = Insurance.query.get(id)
            if not insurance:
                return {'error': 'Insurance not found'}, 404

            data = request.get_json()

            if 'name' in data and data['name'] != insurance.name:
                if Insurance.query.filter_by(name=data['name']).first():
                    return {'error': 'Insurance name already exists'}, 400
                insurance.name = data['name']

            db.session.commit()
            return {'message': 'Insurance updated successfully', 'insurance': insurance.to_dict()}, 200
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

    def delete(self, id):
        try:
            insurance = Insurance.query.get(id)
            if not insurance:
                return {'error': 'Insurance not found'}, 404

            db.session.delete(insurance)
            db.session.commit()
            return {'message': 'Insurance deleted successfully'}, 204
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

# Patient Routes
class Patients(Resource):
    def get(self):
        try:
            patients = [patient.to_dict() for patient in Patient.query.all()]
            return patients, 200
        except Exception as exc:
            return {'error': str(exc)}, 500

    def post(self):
        try:
            data = request.get_json()

            fields = ['id', 'name', 'contact', 'email']
            for field in fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400

            if Patient.query.get(data['id']):
                return {'error': 'Patient ID already exists'}, 400
            if Patient.query.filter_by(contact=data['contact']).first():
                return {'error': 'Contact number already exists'}, 400
            if Patient.query.filter_by(email=data['email']).first():
                return {'error': 'Email already exists'}, 400

            patient = Patient(
                id=data['id'],
                name=data['name'],
                contact=data['contact'],
                email=data['email']
            )
            db.session.add(patient)
            db.session.commit()
            return {'message': 'Patient created successfully', 'patient': patient.to_dict()}, 201
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

class PatientsById(Resource):
    def get(self, id):
        try:
            patient = Patient.query.get(id)
            if not patient:
                return {'error': 'Patient not found'}, 404
            return {'patient': patient.to_dict()}, 200
        except Exception as exc:
            return {'error': str(exc)}, 500

    def patch(self, id):
        try:
            patient = Patient.query.get(id)
            if not patient:
                return {'error': 'Patient not found'}, 404

            data = request.get_json()

            if 'contact' in data and data['contact'] != patient.contact:
                if Patient.query.filter_by(contact=data['contact']).first():
                    return {'error': 'Contact number already exists'}, 400

            if 'email' in data and data['email'] != patient.email:
                if Patient.query.filter_by(email=data['email']).first():
                    return {'error': 'Email already exists'}, 400

            fields = ['name', 'contact', 'email']
            for field in fields:
                if field in data:
                    setattr(patient, field, data[field])

            db.session.commit()
            return {'message': 'Patient updated successfully', 'patient': patient.to_dict()}, 200
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

    def delete(self, id):
        try:
            patient = Patient.query.get(id)
            if not patient:
                return {'error': 'Patient not found'}, 404

            db.session.delete(patient)
            db.session.commit()
            return {'message': 'Patient deleted successfully'}, 204
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

# Review Routes
class Reviews(Resource):
    def get(self):
        try:
            clinic_id = request.args.get('clinic_id')

            query = Review.query
            if clinic_id:
                query = query.filter_by(clinic_id=clinic_id)

            reviews = [review.to_dict() for review in query.all()] 
            return reviews, 200
        except Exception as exc:
            return {'error': str(exc)}, 500

    def post(self):
        try:
            data = request.get_json()

            fields = ['rating', 'clinic_id', 'patient_id']
            for field in fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400

            if not (1 <= data['rating'] <= 5):
                return {'error': 'Rating must be between 1 and 5'}, 400
            if not Clinic.query.get(data['clinic_id']):
                return {'error': 'Clinic not found'}, 404
            if not Patient.query.get(data['patient_id']):
                return {'error': 'Patient not found'}, 404

            review = Review(
                comment=data.get('comment'),
                rating=data['rating'],
                clinic_id=data['clinic_id'],
                patient_id=data['patient_id']
            )
            db.session.add(review)
            db.session.commit()
            return {'message': 'Review created successfully', 'review': review.to_dict()}, 201
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

class ReviewsById(Resource):
    def get(self, id):
        try:
            review = Review.query.get(id)
            if not review:
                return {'error': 'Review not found'}, 404
            return {'review': review.to_dict()}, 200
        except Exception as exc:
            return {'error': str(exc)}, 500

    def patch(self, id):
        try:
            review = Review.query.get(id)
            if not review:
                return {'error': 'Review not found'}, 404

            data = request.get_json()

            if 'rating' in data and not (1 <= data['rating'] <= 5):
                return {'error': 'Rating must be between 1 and 5'}, 400

            fields = ['comment', 'rating']
            for field in fields:
                if field in data:
                    setattr(review, field, data[field])

            db.session.commit()
            return {'message': 'Review updated successfully', 'review': review.to_dict()}, 200
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

    def delete(self, id):
        try:
            review = Review.query.get(id)
            if not review:
                return {'error': 'Review not found'}, 404

            db.session.delete(review)
            db.session.commit()
            return {'message': 'Review deleted successfully'}, 204
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

# Booking Routes
class Bookings(Resource):
    def get(self):
        try:
            clinic_id = request.args.get('clinic_id')
            patient_id = request.args.get('patient_id')
            status = request.args.get('status')

            query = Booking.query

            if clinic_id:
                query = query.filter_by(clinic_id=clinic_id)
            if patient_id:
                query = query.filter_by(patient_id=patient_id)
            if status:
                query = query.filter_by(status=status)

            bookings = [booking.to_dict() for booking in query.all()]
            return bookings, 200
        except Exception as exc:
            return {'error': str(exc)}, 500

    def post(self):
        try:
            data = request.get_json()

            fields = ['appointment_date', 'clinic_id',
                      'service_id', 'patient_id']
            for field in fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400

            try:
                appointment_date = datetime.strptime(
                    data['appointment_date'], '%Y-%m-%d %H:%M')
                if appointment_date <= datetime.now():
                    return {'error': 'Appointment date must be in the future'}, 400
            except (ValueError, TypeError):
                return {'error': 'Invalid appointment date format. Use YYYY-MM-DD HH:MM'}, 400

            if not Clinic.query.get(data['clinic_id']):
                return {'error': 'Clinic not found'}, 404
            if not Service.query.get(data['service_id']):
                return {'error': 'Service not found'}, 404
            if not Patient.query.get(data['patient_id']):
                return {'error': 'Patient not found'}, 404

            statuses = ['pending', 'confirmed', 'cancelled', 'completed']
            status = data.get('status', 'pending')
            if status not in statuses:
                return {'error': f'Invalid status. Must be one of: {", ".join(statuses)}'}, 400

            booking = Booking(
                booking_date=datetime.now(),
                appointment_date=appointment_date,
                status=status,
                notes=data.get('notes'),
                clinic_id=data['clinic_id'],
                service_id=data['service_id'],
                patient_id=data['patient_id']
            )

            db.session.add(booking)
            db.session.commit()
            return {'message': 'Booking created successfully', 'booking': booking.to_dict()}, 201
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

class BookingsById(Resource):
    def get(self, id):
        try:
            booking = Booking.query.get(id)
            if not booking:
                return {'error': 'Booking not found'}, 404
            return {'booking': booking.to_dict()}, 200
        except Exception as exc:
            return {'error': str(exc)}, 500

    def patch(self, id):
        try:
            booking = Booking.query.get(id)
            if not booking:
                return {'error': 'Booking not found'}, 404

            data = request.get_json()

            if 'appointment_date' in data:
                try:
                    appointment_date = datetime.strptime(
                        data['appointment_date'], '%Y-%m-%d %H:%M')
                    if appointment_date <= datetime.now():
                        return {'error': 'Appointment date must be in the future'}, 400
                except (ValueError, TypeError):
                    return {'error': 'Invalid appointment date format. Use YYYY-MM-DD HH:MM'}, 400

            if 'status' in data:
                statuses = ['pending', 'confirmed', 'cancelled', 'completed']
                if data['status'] not in statuses:
                    return {'error': f'Invalid status. Must be one of: {", ".join(statuses)}'}, 400
                booking.status = data['status']

            if 'notes' in data:
                booking.notes = data['notes']

            db.session.commit()
            return {'message': 'Booking updated successfully', 'booking': booking.to_dict()}, 200
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

    def delete(self, id):
        try:
            booking = Booking.query.get(id)
            if not booking:
                return {'error': 'Booking not found'}, 404

            db.session.delete(booking)
            db.session.commit()
            return {'message': 'Booking deleted successfully'}, 204

        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

# Many-to-Many Relationship Routes
class ClinicServicesById(Resource):
    def post(self, clinic_id):
        try:
            data = request.get_json()

            if 'service_id' not in data:
                return {'error': 'Missing required field: service_id'}, 400

            clinic = Clinic.query.get(clinic_id)
            service = Service.query.get(data['service_id'])

            if not clinic:
                return {'error': 'Clinic not found'}, 404
            if not service:
                return {'error': 'Service not found'}, 404

            if service in clinic.services:
                return {'error': 'Service already associated with this clinic'}, 400

            clinic.services.append(service)
            db.session.commit()

            return {'message': 'Service added to clinic successfully'}, 201
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

    def delete(self, clinic_id):
        try:
            data = request.get_json()

            if 'service_id' not in data:
                return {'error': 'Missing required field: service_id'}, 400

            clinic = Clinic.query.get(clinic_id)
            service = Service.query.get(data['service_id'])

            if not clinic:
                return {'error': 'Clinic not found'}, 404
            if not service:
                return {'error': 'Service not found'}, 404

            if service not in clinic.services:
                return {'error': 'Service not associated with this clinic'}, 400

            clinic.services.remove(service)
            db.session.commit()

            return {'message': 'Service removed from clinic successfully'}, 204
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

class ClinicInsurancesById(Resource):
    def post(self, clinic_id):
        try:
            data = request.get_json()

            if 'insurance_id' not in data:
                return {'error': 'Missing required field: insurance_id'}, 400

            clinic = Clinic.query.get(clinic_id)
            insurance = Insurance.query.get(data['insurance_id'])

            if not clinic:
                return {'error': 'Clinic not found'}, 404
            if not insurance:
                return {'error': 'Insurance not found'}, 404
            if insurance in clinic.insurance_accepted:
                return {'error': 'Insurance already associated with this clinic'}, 400

            clinic.insurance_accepted.append(insurance)
            db.session.commit()

            return {'message': 'Insurance added to clinic successfully'}, 201
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

    def delete(self, clinic_id):
        try:
            data = request.get_json()

            if 'insurance_id' not in data:
                return {'error': 'Missing required field: insurance_id'}, 400

            clinic = Clinic.query.get(clinic_id)
            insurance = Insurance.query.get(data['insurance_id'])

            if not clinic:
                return {'error': 'Clinic not found'}, 404
            if not insurance:
                return {'error': 'Insurance not found'}, 404
            if insurance not in clinic.insurance_accepted:
                return {'error': 'Insurance not associated with this clinic'}, 400

            clinic.insurance_accepted.remove(insurance)
            db.session.commit()

            return {'message': 'Insurance removed from clinic successfully'}, 204
        except Exception as exc:
            db.session.rollback()
            return {'error': str(exc)}, 500

# API routes
api.add_resource(Clinics, '/clinics')
api.add_resource(ClinicsById, '/clinics/<int:id>')
api.add_resource(Services, '/services')
api.add_resource(ServicesById, '/services/<int:id>')
api.add_resource(Insurances, '/insurances')
api.add_resource(InsurancesById, '/insurances/<int:id>')
api.add_resource(Patients, '/patients')
api.add_resource(PatientsById, '/patients/<int:id>')
api.add_resource(Reviews, '/reviews')
api.add_resource(ReviewsById, '/reviews/<int:id>')
api.add_resource(Bookings, '/bookings')
api.add_resource(BookingsById, '/bookings/<int:id>')
api.add_resource(ClinicServicesById, '/clinics/<int:clinic_id>/services')
api.add_resource(ClinicInsurancesById, '/clinics/<int:clinic_id>/insurances')

# Initialize DB and run app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create initial admin user if none exists
        if not User.query.filter_by(role='admin').first():
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)