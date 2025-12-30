"""
API Routes for Interest Rate Monitor
Provides RESTful endpoints for rate data, AI analysis, and news.
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
import logging
import json
import os

from app.services.rate_service import get_rate_service
from app.services.ai_analysis_service import get_ai_service
from app.services.news_service import get_news_service
from app.services.chat_service import get_chat_service
from app.services.dart_service import get_dart_service

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


def create_response(status: str, data=None, error: str = None):
    """Create standardized API response."""
    response = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }
    if data is not None:
        response["data"] = data
    if error:
        response["error"] = error
    return response


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@api_bp.route('/rates', methods=['GET'])
def get_rates():
    """
    Get historical interest rate data.
    
    Query Parameters:
        days (int): Number of days of data (default: 90, max: 365)
        
    Returns:
        JSON with US/Korean rates and spread data
    """
    try:
        days = request.args.get('days', 90, type=int)
        days = min(max(days, 1), 365)  # Clamp between 1 and 365
        
        rate_service = get_rate_service()
        combined_data = rate_service.get_combined_rates(days=days)
        
        if combined_data.empty:
            return jsonify(create_response(
                status="error",
                error="No rate data available"
            )), 404
        
        # Convert to JSON-serializable format
        records = []
        for _, row in combined_data.iterrows():
            records.append({
                "date": row["date"].strftime("%Y-%m-%d"),
                "us_rate": round(float(row["us_rate"]), 3),
                "kr_rate": round(float(row["kr_rate"]), 3),
                "spread": round(float(row["spread"]), 1)
            })
        
        return jsonify(create_response(
            status="success",
            data={
                "rates": records,
                "count": len(records),
                "period_days": days
            }
        ))
        
    except Exception as e:
        logger.error(f"Error fetching rates: {e}")
        return jsonify(create_response(
            status="error",
            error="Failed to fetch rate data"
        )), 500


@api_bp.route('/rates/latest', methods=['GET'])
def get_latest_rates():
    """
    Get the most recent rate data.
    
    Returns:
        JSON with latest US rate, Korean rate, and spread
    """
    try:
        rate_service = get_rate_service()
        latest = rate_service.get_latest_rates()
        
        if latest.get("error"):
            return jsonify(create_response(
                status="error",
                error=latest["error"]
            )), 404
        
        return jsonify(create_response(
            status="success",
            data=latest
        ))
        
    except Exception as e:
        logger.error(f"Error fetching latest rates: {e}")
        return jsonify(create_response(
            status="error",
            error="Failed to fetch latest rate data"
        )), 500


@api_bp.route('/analysis', methods=['GET'])
def get_analysis():
    """
    Get AI-generated market analysis.

    Returns:
        JSON with analysis text and metadata
    """
    try:
        rate_service = get_rate_service()
        ai_service = get_ai_service()
        news_service = get_news_service()

        # Get rate data for analysis
        combined_data = rate_service.get_combined_rates(days=30)

        if combined_data.empty:
            return jsonify(create_response(
                status="error",
                error="Insufficient rate data for analysis"
            )), 404

        # Prepare data for analysis
        us_rates = combined_data[["date", "us_rate"]].copy()
        kr_rates = combined_data[["date", "kr_rate"]].copy()
        current_spread = combined_data.iloc[-1]["spread"]

        # Get news data for analysis
        us_news = news_service.get_us_rate_news(limit=5)
        kr_news = news_service.get_kr_rate_news(limit=5)

        # Generate analysis with news context
        analysis_text = ai_service.generate_rate_analysis(
            us_rates=us_rates,
            kr_rates=kr_rates,
            spread=current_spread,
            us_news=us_news,
            kr_news=kr_news
        )

        return jsonify(create_response(
            status="success",
            data={
                "analysis": analysis_text,
                "generated_at": datetime.now().isoformat(),
                "data_date": combined_data.iloc[-1]["date"].strftime("%Y-%m-%d")
            }
        ))

    except Exception as e:
        logger.error(f"Error generating analysis: {e}")
        return jsonify(create_response(
            status="error",
            error="Failed to generate analysis"
        )), 500


@api_bp.route('/news', methods=['GET'])
def get_news():
    """
    Get interest rate related news.
    
    Query Parameters:
        country (str): 'us', 'kr', or 'all' (default: 'all')
        limit (int): Number of news items per country (default: 5, max: 10)
        
    Returns:
        JSON with news items
    """
    try:
        country = request.args.get('country', 'all').lower()
        limit = request.args.get('limit', 5, type=int)
        limit = min(max(limit, 1), 10)  # Clamp between 1 and 10
        
        news_service = get_news_service()
        
        if country == 'us':
            news_data = {"us": news_service.get_us_rate_news(limit)}
        elif country == 'kr':
            news_data = {"kr": news_service.get_kr_rate_news(limit)}
        else:
            news_data = news_service.get_all_news(limit)
        
        # Add relative time to each news item
        for country_key in news_data:
            for item in news_data[country_key]:
                item["relative_time"] = news_service.get_relative_time(
                    item.get("published_at", "")
                )
        
        return jsonify(create_response(
            status="success",
            data=news_data
        ))
        
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return jsonify(create_response(
            status="error",
            error="Failed to fetch news"
        )), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON with service status
    """
    return jsonify(create_response(
        status="success",
        data={
            "service": "Interest Rate Monitor API",
            "version": "1.0.0",
            "healthy": True
        }
    ))


@api_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """
    Clear all service caches.

    Returns:
        JSON confirmation
    """
    try:
        get_rate_service().clear_cache()
        get_ai_service().clear_cache()
        get_news_service().clear_cache()

        return jsonify(create_response(
            status="success",
            data={"message": "All caches cleared"}
        ))

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify(create_response(
            status="error",
            error="Failed to clear cache"
        )), 500


@api_bp.route('/forecast', methods=['GET'])
def get_forecast():
    """
    Get analyst forecast data for interest rates.

    Returns:
        JSON with 12-month forecast data
    """
    try:
        # Get the path to forecast.json
        forecast_path = os.path.join(
            current_app.root_path,
            '..',
            'static',
            'data',
            'forecast.json'
        )
        forecast_path = os.path.normpath(forecast_path)

        if not os.path.exists(forecast_path):
            return jsonify(create_response(
                status="error",
                error="Forecast data not found"
            )), 404

        with open(forecast_path, 'r', encoding='utf-8') as f:
            forecast_data = json.load(f)

        return jsonify(create_response(
            status="success",
            data=forecast_data
        ))

    except Exception as e:
        logger.error(f"Error fetching forecast: {e}")
        return jsonify(create_response(
            status="error",
            error="Failed to fetch forecast data"
        )), 500


@api_bp.route('/chat', methods=['POST'])
def chat():
    """
    Chat with AI about interest rates using Groq + Qwen3 32B.

    Request Body:
        message (str): User's chat message

    Returns:
        JSON with AI response
    """
    try:
        data = request.get_json()
        if not data or not data.get('message'):
            return jsonify(create_response(
                status="error",
                error="Message is required"
            )), 400

        message = data['message'].strip()
        if len(message) > 500:
            return jsonify(create_response(
                status="error",
                error="Message too long (max 500 characters)"
            )), 400

        # Get services
        rate_service = get_rate_service()
        news_service = get_news_service()
        chat_service = get_chat_service()

        # Get current rate context
        rate_context = None
        try:
            latest = rate_service.get_latest_rates()
            if not latest.get("error"):
                rate_context = {
                    "us_rate": latest.get("us_rate"),
                    "kr_rate": latest.get("kr_rate"),
                    "spread": latest.get("spread")
                }
        except Exception:
            pass  # Continue without rate context

        # Get news context
        us_news = None
        kr_news = None
        try:
            us_news = news_service.get_us_rate_news(limit=7)
            kr_news = news_service.get_kr_rate_news(limit=7)
        except Exception:
            pass  # Continue without news context

        # Generate response using Groq + Qwen3
        response_text = chat_service.chat(
            message=message,
            rate_context=rate_context,
            us_news=us_news,
            kr_news=kr_news
        )

        return jsonify(create_response(
            status="success",
            data={
                "response": response_text,
                "timestamp": datetime.now().isoformat()
            }
        ))

    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return jsonify(create_response(
            status="error",
            error="Failed to process chat message"
        )), 500


# ============================================================================
# DART API Endpoints - 보험사 듀레이션 분석
# ============================================================================

@api_bp.route('/dart/companies', methods=['GET'])
def get_dart_companies():
    """
    Get list of insurance companies available for DART analysis.

    Returns:
        JSON with company list
    """
    try:
        dart_service = get_dart_service()
        companies = dart_service.get_company_list()

        return jsonify(create_response(
            status="success",
            data={"companies": companies}
        ))

    except Exception as e:
        logger.error(f"Error fetching companies: {e}")
        return jsonify(create_response(
            status="error",
            error="Failed to fetch company list"
        )), 500


@api_bp.route('/dart/analyze', methods=['POST'])
def analyze_dart():
    """
    Analyze equity-rate duration for insurance companies.

    Request Body:
        company_id (str): Company ID (samsung, hanwha, kyobo, shinhan)
        year_count (int): Number of years to analyze (default: 3)

    Returns:
        JSON with duration analysis results
    """
    try:
        data = request.get_json() or {}
        company_id = data.get('company_id', 'samsung')
        year_count = data.get('year_count', 3)

        # Validate inputs
        valid_companies = ['samsung', 'hanwha', 'kyobo', 'shinhan']
        if company_id not in valid_companies:
            return jsonify(create_response(
                status="error",
                error=f"Invalid company_id. Must be one of: {', '.join(valid_companies)}"
            )), 400

        year_count = min(max(year_count, 1), 5)  # Clamp between 1 and 5

        # Get services
        dart_service = get_dart_service()
        rate_service = get_rate_service()

        # 1. Get equity data from DART
        logger.info(f"Fetching equity data for {company_id}, {year_count} years")
        equity_data = dart_service.get_equity_data(company_id, year_count)

        logger.info(f"Received {len(equity_data) if equity_data else 0} quarters of data")

        if not equity_data or len(equity_data) < 2:
            error_msg = f"Insufficient equity data for {company_id} (minimum 2 quarters required, got {len(equity_data) if equity_data else 0})"
            logger.error(error_msg)
            return jsonify(create_response(
                status="error",
                error=error_msg
            )), 400

        # 2. Get quarter dates
        quarters = [item['quarter'] for item in equity_data]
        equity_levels = [item['equity'] for item in equity_data]
        asset_levels = [item.get('asset') for item in equity_data]
        liability_levels = [item.get('liability') for item in equity_data]

        # 3. Get rate data for the same quarters
        us10y_rates = {}
        kr10y_rates = {}

        for quarter in quarters:
            try:
                # Get rate data around the quarter end date
                from datetime import datetime, timedelta
                q_date = datetime.strptime(quarter, '%Y-%m-%d')

                # Get 10 days of data around the quarter end
                start_date = q_date - timedelta(days=10)
                end_date = q_date

                rate_data = rate_service.get_combined_rates(
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )

                if not rate_data.empty:
                    # Use the last available rate (closest to quarter end)
                    last_row = rate_data.iloc[-1]
                    us10y_rates[quarter] = float(last_row['us_rate'])
                    kr10y_rates[quarter] = float(last_row['kr_rate'])

            except Exception as e:
                logger.warning(f"Error fetching rate for quarter {quarter}: {e}")
                continue

        # 4. Calculate durations
        us_duration_series, us_duration_summary = dart_service.calculate_duration(
            equity_data, us10y_rates
        )
        kr_duration_series, kr_duration_summary = dart_service.calculate_duration(
            equity_data, kr10y_rates
        )

        # 5. Calculate changes (QoQ)
        equity_qoq = [None]
        for i in range(1, len(equity_levels)):
            if equity_levels[i-1] and equity_levels[i-1] != 0:
                change = (equity_levels[i] / equity_levels[i-1]) - 1
                equity_qoq.append(round(change, 6))
            else:
                equity_qoq.append(None)

        us10y_levels = [us10y_rates.get(q) for q in quarters]
        kr10y_levels = [kr10y_rates.get(q) for q in quarters]

        us10y_change = [None]
        for i in range(1, len(us10y_levels)):
            if us10y_levels[i] is not None and us10y_levels[i-1] is not None:
                change = (us10y_levels[i] / 100) - (us10y_levels[i-1] / 100)
                us10y_change.append(round(change, 6))
            else:
                us10y_change.append(None)

        kr10y_change = [None]
        for i in range(1, len(kr10y_levels)):
            if kr10y_levels[i] is not None and kr10y_levels[i-1] is not None:
                change = (kr10y_levels[i] / 100) - (kr10y_levels[i-1] / 100)
                kr10y_change.append(round(change, 6))
            else:
                kr10y_change.append(None)

        # 6. Convert to 억원 units
        equity_billions = [round(e / 100000000, 1) if e else None for e in equity_levels]
        asset_billions = [round(a / 100000000, 1) if a else None for a in asset_levels]
        liability_billions = [round(l / 100000000, 1) if l else None for l in liability_levels]

        # 7. Build response
        from app.services.dart_service import COMPANY_MAP
        company_name = COMPANY_MAP[company_id]['name']

        response_data = {
            "company": company_name,
            "quarters": quarters,
            "equity_level": equity_billions,
            "asset_level": asset_billions,
            "liability_level": liability_billions,
            "us10y_level": us10y_levels,
            "kr10y_level": kr10y_levels,
            "equity_qoq": equity_qoq,
            "us10y_change": us10y_change,
            "kr10y_change": kr10y_change,
            "duration": {
                "us10y": {
                    "series": us_duration_series,
                    "summary": us_duration_summary
                },
                "kr10y": {
                    "series": kr_duration_series,
                    "summary": kr_duration_summary
                }
            },
            "analysis_count": len([d for d in us_duration_series if d is not None])
        }

        return jsonify(create_response(
            status="success",
            data=response_data
        ))

    except ValueError as e:
        logger.error(f"Validation error in DART analysis: {e}")
        return jsonify(create_response(
            status="error",
            error=str(e)
        )), 400

    except Exception as e:
        logger.error(f"Error in DART analysis: {e}", exc_info=True)
        return jsonify(create_response(
            status="error",
            error=f"Failed to perform DART analysis: {str(e)}"
        )), 500
