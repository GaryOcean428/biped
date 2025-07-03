"""
Advanced Data Pipeline and Analytics Service
Implements real-time data processing, analytics, and business intelligence
"""

import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import redis
from flask import current_app

from ..utils.redis_client import redis_client
from ..utils.performance import TradingCacheService

logger = logging.getLogger(__name__)

@dataclass
class ServiceDataPoint:
    """Service marketplace data point structure"""
    service_id: str
    timestamp: datetime
    category: str
    location: str
    price_min: float
    price_max: float
    demand_score: float
    supply_score: float
    completion_rate: float
    avg_rating: float
    response_time: float

@dataclass
class JobEvent:
    """Job marketplace event structure"""
    job_id: str
    user_id: str
    provider_id: str
    category: str
    status: str  # 'posted', 'quoted', 'assigned', 'completed'
    value: float
    timestamp: datetime
    location: str
    urgency: str
    metadata: Dict[str, Any]

@dataclass
class MarketplaceMetrics:
    """Marketplace analytics metrics structure"""
    timestamp: datetime
    category: str
    job_volume_24h: int
    avg_job_value: float
    completion_rate: float
    avg_response_time: float
    provider_availability: float
    customer_satisfaction: float
    price_trend: float
    demand_supply_ratio: float
    seasonal_factor: float

class RealTimeDataProcessor:
    """Real-time marketplace data processing engine"""
    
    def __init__(self, cache_service: TradingCacheService):
        self.cache_service = cache_service
        self.data_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.is_running = True
        self.start_time = datetime.utcnow()
        self.processing_stats = {
            'processed_events': 0,
            'processing_errors': 0,
            'last_update': datetime.utcnow()
        }
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def start_processing(self):
        """Start real-time marketplace data processing"""
        self.is_running = True
        
        # Start processing tasks
        tasks = [
            self._process_service_data_stream(),
            self._process_job_events(),
            self._calculate_real_time_metrics(),
            self._detect_anomalies(),
            self._update_analytics_cache()
        ]
        
        await asyncio.gather(*tasks)
    
    async def _process_service_data_stream(self):
        """Process incoming service marketplace data"""
        while self.is_running:
            try:
                # Simulate service data (in production, this would come from database)
                service_data = await self._fetch_service_data()
                
                for category, data in service_data.items():
                    # Add to buffer
                    self.data_buffer[f"service:{category}"].append(data)
                    
                    # Calculate real-time metrics
                    metrics = self._calculate_category_metrics(category, data)
                    
                    # Cache metrics
                    if self.cache_service:
                        cache_key = f"service_data:{category}"
                        service_data_dict = {
                            'avg_price': (data.price_min + data.price_max) / 2,
                            'demand_score': data.demand_score,
                            'supply_score': data.supply_score,
                            'completion_rate': data.completion_rate,
                            'avg_rating': data.avg_rating,
                            'response_time': data.response_time,
                            'timestamp': data.timestamp.isoformat(),
                            'metrics': metrics
                        }
                        try:
                            self.cache_service.set(cache_key, service_data_dict, timeout=60)
                        except Exception as cache_error:
                            logger.debug(f"Cache storage failed: {cache_error}")
                    
                    # Update processing stats
                    self.processing_stats['processed_events'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing service data: {e}")
                self.processing_stats['processing_errors'] += 1
                
            await asyncio.sleep(1)  # Process every second
    
    async def _process_job_events(self):
        """Process job events for analytics"""
        while self.is_running:
            try:
                # Get recent jobs from database
                jobs = await self._fetch_recent_jobs()
                
                for job in jobs:
                    # Add to buffer
                    self.data_buffer[f"jobs:{job.category}"].append(job)
                    
                    # Calculate job metrics
                    metrics = self._calculate_job_metrics(job)
                    
                    # Update user analytics
                    await self._update_user_analytics(job.user_id, job)
                    
                    # Check for unusual patterns
                    anomaly_score = self._detect_job_anomaly(job)
                    if anomaly_score > 0.8:
                        await self._flag_suspicious_job(job, anomaly_score)
                        
            except Exception as e:
                logger.error(f"Error processing job events: {e}")
                
            await asyncio.sleep(5)  # Process every 5 seconds
    
    def _calculate_job_metrics(self, job) -> Dict:
        """Calculate metrics for a job"""
        try:
            # Calculate job-specific metrics
            metrics = {
                'value_category': 'high' if job.value > 5000 else 'medium' if job.value > 1000 else 'low',
                'urgency_factor': 2.0 if job.urgency == 'urgent' else 1.0,
                'location_demand': 1.0  # Would be calculated from historical data
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating job metrics: {e}")
            return {}
    
    def _detect_job_anomaly(self, job) -> float:
        """Detect if a job posting is anomalous (returns score 0-1)"""
        try:
            # Simple anomaly detection based on job value and pattern
            if job.value > 50000:  # Very high value job
                return 0.9
            elif job.value > 20000:
                return 0.6
            else:
                return 0.1
        except Exception as e:
            logger.error(f"Error detecting job anomaly: {e}")
            return 0.0
    
    async def _update_user_analytics(self, user_id: str, job):
        """Update user analytics with new job"""
        try:
            # Cache user job data
            if self.cache_service:
                user_key = f"user_jobs:{user_id}"
                # In production, this would update user analytics
                logger.debug(f"Updated analytics for user {user_id}")
        except Exception as e:
            logger.error(f"Error updating user analytics: {e}")
    
    async def _flag_suspicious_job(self, job, anomaly_score: float):
        """Flag a suspicious job for review"""
        try:
            suspicious_job = {
                'job_id': getattr(job, 'job_id', 'unknown'),
                'user_id': job.user_id,
                'category': job.category,
                'value': job.value,
                'location': job.location,
                'anomaly_score': anomaly_score,
                'timestamp': job.timestamp.isoformat(),
                'flagged_at': datetime.utcnow().isoformat()
            }
            
            if self.cache_service:
                try:
                    self.cache_service.set(f"suspicious_job:{job.user_id}", suspicious_job, timeout=3600)
                except Exception as cache_error:
                    logger.debug(f"Cache storage failed: {cache_error}")
            
            logger.warning(f"Flagged suspicious job: {suspicious_job}")
        except Exception as e:
            logger.error(f"Error flagging suspicious job: {e}")
    
    async def _calculate_real_time_metrics(self):
        """Calculate real-time metrics for all active service categories"""
        while True:
            try:
                # Get all active categories from data buffer
                active_categories = set()
                for key in self.data_buffer.keys():
                    if key.startswith('service:'):
                        category = key.replace('service:', '')
                        active_categories.add(category)
                
                # Calculate metrics for each category
                for category in active_categories:
                    if category in self.data_buffer.get(f"service:{category}", []):
                        latest_data = self.data_buffer[f"service:{category}"][-1] if self.data_buffer[f"service:{category}"] else None
                        if latest_data:
                            metrics = self._calculate_category_metrics(category, latest_data)
                            
                            # Store metrics in cache
                            cache_key = f"metrics:{category}"
                            if self.cache_service:
                                self.cache_service.set(cache_key, metrics, timeout=60)
                            
                            logger.debug(f"Updated metrics for {category}: {metrics}")
                
            except Exception as e:
                logger.error(f"Error calculating real-time metrics: {e}")
                
            await asyncio.sleep(30)  # Update metrics every 30 seconds

    def _calculate_category_metrics(self, category: str, data: ServiceDataPoint) -> Dict:
        """Calculate marketplace metrics for a service category"""
        buffer = self.data_buffer[f"service:{category}"]
        
        if len(buffer) < 5:  # Need minimum data points
            return {}
            
        # Convert to pandas for calculations
        df = pd.DataFrame([asdict(point) for point in buffer])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        metrics = {}
        
        try:
            # Price trends
            if len(df) >= 2:
                avg_prices = [(row['price_min'] + row['price_max']) / 2 for _, row in df.iterrows()]
                if len(avg_prices) >= 2:
                    metrics['price_trend'] = ((avg_prices[-1] - avg_prices[0]) / avg_prices[0]) * 100
            
            # Demand/Supply metrics
            if len(df) >= 5:
                metrics['avg_demand_score'] = df['demand_score'].mean()
                metrics['avg_supply_score'] = df['supply_score'].mean()
                metrics['demand_supply_ratio'] = metrics['avg_demand_score'] / max(metrics['avg_supply_score'], 0.1)
            
            # Service quality metrics
            metrics['avg_completion_rate'] = df['completion_rate'].mean()
            metrics['avg_rating'] = df['avg_rating'].mean()
            metrics['avg_response_time'] = df['response_time'].mean()
            
            # Volatility in pricing
            if len(df) >= 10:
                avg_prices_series = pd.Series([(row['price_min'] + row['price_max']) / 2 for _, row in df.iterrows()])
                price_changes = avg_prices_series.pct_change().dropna()
                metrics['price_volatility'] = price_changes.std() * 100
            
            # Capacity metrics
            if 'supply_score' in df.columns:
                metrics['capacity_utilization'] = (1 - df['supply_score'].mean()) * 100  # Lower supply = higher utilization
            
        except Exception as e:
            logger.error(f"Error calculating metrics for {category}: {e}")
            
        return metrics
    
    async def _fetch_service_data(self) -> Dict[str, ServiceDataPoint]:
        """Fetch service marketplace data (simulated for demo)"""
        categories = ['Plumbing', 'Electrical', 'Carpentry', 'Painting', 'Landscaping', 'Cleaning']
        service_data = {}
        
        for category in categories:
            # Simulate realistic service data
            base_price_min = self._get_base_price_range(category)[0]
            base_price_max = self._get_base_price_range(category)[1]
            
            # Add some variation
            price_variation = np.random.normal(0, 0.1)  # 10% variation
            current_min = base_price_min * (1 + price_variation)
            current_max = base_price_max * (1 + price_variation)
            
            service_data[category] = ServiceDataPoint(
                service_id=f"cat_{category.lower()}",
                timestamp=datetime.utcnow(),
                category=category,
                location="Various",
                price_min=max(current_min, 50),  # Minimum $50
                price_max=current_max,
                demand_score=np.random.uniform(0.3, 0.9),
                supply_score=np.random.uniform(0.2, 0.8),
                completion_rate=np.random.uniform(0.8, 0.98),
                avg_rating=np.random.uniform(4.0, 4.9),
                response_time=np.random.uniform(1, 24)  # Hours
            )
            
        return service_data
    
    def _get_base_price_range(self, category: str) -> Tuple[float, float]:
        """Get base price range for service category"""
        price_ranges = {
            'Plumbing': (100, 500),
            'Electrical': (150, 800),
            'Carpentry': (200, 1200),
            'Painting': (80, 400),
            'Landscaping': (120, 600),
            'Cleaning': (60, 200)
        }
        return price_ranges.get(category, (100, 300))
    
    async def _fetch_recent_jobs(self) -> List:
        """Fetch recent jobs (simulated for demo)"""
        # In production, this would query the database
        jobs = []
        categories = ['Plumbing', 'Electrical', 'Carpentry', 'Painting']
        
        for _ in range(5):  # Simulate 5 recent jobs
            job = type('Job', (), {
                'job_id': f"job_{np.random.randint(1000, 9999)}",
                'category': np.random.choice(categories),
                'status': np.random.choice(['posted', 'quoted', 'assigned', 'completed']),
                'value': np.random.uniform(200, 5000),
                'location': np.random.choice(['Sydney', 'Melbourne', 'Brisbane', 'Perth']),
                'urgency': np.random.choice(['normal', 'urgent']),
                'timestamp': datetime.utcnow(),
                'user_id': f"user_{np.random.randint(1, 100)}",
                'provider_id': f"provider_{np.random.randint(1, 50)}"
            })()
            jobs.append(job)
        
        return jobs
    
    async def _detect_anomalies(self):
        """Detect anomalies in marketplace data and job patterns"""
        while self.is_running:
            try:
                # Check for unusual pricing or demand patterns
                for category in ['Plumbing', 'Electrical', 'Carpentry', 'Painting']:
                    buffer_key = f"service:{category}"
                    if buffer_key in self.data_buffer and len(self.data_buffer[buffer_key]) > 5:
                        recent_data = self.data_buffer[buffer_key][-5:]
                        avg_prices = [(point.price_min + point.price_max) / 2 for point in recent_data]
                        
                        # Calculate price volatility
                        if len(avg_prices) >= 2:
                            price_changes = [abs((avg_prices[i] - avg_prices[i-1]) / avg_prices[i-1]) for i in range(1, len(avg_prices))]
                            avg_volatility = np.mean(price_changes)
                            
                            # Flag if pricing volatility is unusually high
                            if avg_volatility > 0.2:  # 20% threshold
                                logger.warning(f"High pricing volatility detected in {category}: {avg_volatility:.2%}")
                                
                                # Store anomaly
                                anomaly = {
                                    'type': 'pricing_volatility',
                                    'category': category,
                                    'volatility': avg_volatility,
                                    'timestamp': datetime.utcnow().isoformat()
                                }
                                
                                if self.cache_service:
                                    try:
                                        self.cache_service.set(f"anomaly:{category}", anomaly, timeout=300)
                                    except Exception as cache_error:
                                        logger.debug(f"Cache storage failed: {cache_error}")
                
                # Check for demand/supply imbalances
                for category in ['Plumbing', 'Electrical', 'Carpentry', 'Painting']:
                    buffer_key = f"service:{category}"
                    if buffer_key in self.data_buffer and len(self.data_buffer[buffer_key]) > 3:
                        recent_data = self.data_buffer[buffer_key][-3:]
                        avg_demand = np.mean([point.demand_score for point in recent_data])
                        avg_supply = np.mean([point.supply_score for point in recent_data])
                        
                        # Flag significant imbalances
                        if avg_demand > 0.8 and avg_supply < 0.3:
                            logger.warning(f"High demand, low supply detected in {category}")
                        elif avg_demand < 0.3 and avg_supply > 0.8:
                            logger.info(f"Low demand, high supply detected in {category}")
                
            except Exception as e:
                logger.error(f"Error detecting anomalies: {e}")
                
            await asyncio.sleep(60)  # Check every minute
    
    async def _update_analytics_cache(self):
        """Update analytics cache with marketplace data"""
        while self.is_running:
            try:
                # Update marketplace summary
                marketplace_summary = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'active_categories': len([k for k in self.data_buffer.keys() if k.startswith('service:')]),
                    'total_events_processed': self.processing_stats['processed_events'],
                    'processing_errors': self.processing_stats['processing_errors'],
                    'uptime': (datetime.utcnow() - self.start_time).total_seconds()
                }
                
                if self.cache_service:
                    try:
                        self.cache_service.set('marketplace_summary', marketplace_summary, timeout=300)
                    except Exception as cache_error:
                        logger.debug(f"Cache storage failed: {cache_error}")
                
                # Update trending services
                trending_services = await self._calculate_trending_services()
                if self.cache_service:
                    try:
                        self.cache_service.set('trending_services', trending_services, timeout=300)
                    except Exception as cache_error:
                        logger.debug(f"Cache storage failed: {cache_error}")
                
            except Exception as e:
                logger.error(f"Error updating analytics cache: {e}")
                
            await asyncio.sleep(300)  # Update every 5 minutes
    
    async def _calculate_trending_services(self) -> Dict:
        """Calculate trending service categories"""
        trends = {'high_demand': [], 'good_value': []}
        
        for category in ['Plumbing', 'Electrical', 'Carpentry', 'Painting', 'Landscaping', 'Cleaning']:
            buffer_key = f"service:{category}"
            if buffer_key in self.data_buffer and len(self.data_buffer[buffer_key]) >= 2:
                recent_data = self.data_buffer[buffer_key][-2:]
                if len(recent_data) >= 2:
                    # Calculate demand trend
                    demand_change = recent_data[-1].demand_score - recent_data[0].demand_score
                    avg_price = (recent_data[-1].price_min + recent_data[-1].price_max) / 2
                    
                    trend_data = {
                        'category': category,
                        'avg_price': avg_price,
                        'demand_score': recent_data[-1].demand_score,
                        'completion_rate': recent_data[-1].completion_rate,
                        'avg_rating': recent_data[-1].avg_rating,
                        'demand_change': demand_change
                    }
                    
                    if demand_change > 0.1:  # Significant demand increase
                        trends['high_demand'].append(trend_data)
                    
                    if recent_data[-1].completion_rate > 0.9 and recent_data[-1].avg_rating > 4.5:
                        trends['good_value'].append(trend_data)
        
        # Sort by relevance
        trends['high_demand'] = sorted(trends['high_demand'], key=lambda x: x['demand_change'], reverse=True)[:5]
        trends['good_value'] = sorted(trends['good_value'], key=lambda x: x['avg_rating'], reverse=True)[:5]
        
        return trends

class MarketplaceIntelligenceEngine:
    """Marketplace Intelligence and Reporting Engine"""
    
    def __init__(self, cache_service: TradingCacheService):
        self.cache_service = cache_service
        self.report_cache = {}
        
    async def generate_user_analytics(self, user_id: str) -> Dict:
        """Generate comprehensive user analytics for marketplace activity"""
        try:
            # Get user jobs and provider interactions
            jobs = await self._get_user_jobs(user_id)
            reviews = await self._get_user_reviews(user_id, days=30)
            
            analytics = {
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'job_summary': self._calculate_job_summary(jobs),
                'service_preferences': self._analyze_service_preferences(jobs),
                'satisfaction_metrics': self._calculate_satisfaction_metrics(reviews),
                'spending_analysis': self._analyze_spending_patterns(jobs),
                'activity_patterns': self._analyze_activity_patterns(jobs),
                'recommendations': self._generate_user_recommendations(jobs, reviews)
            }
            
            # Cache analytics
            if self.cache_service:
                try:
                    self.cache_service.set(f"user_analytics:{user_id}", analytics, timeout=3600)
                except Exception as cache_error:
                    logger.debug(f"Cache storage failed: {cache_error}")
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating user analytics for {user_id}: {e}")
            return {'error': str(e)}
    
    def _calculate_job_summary(self, jobs: List[Dict]) -> Dict:
        """Calculate job summary metrics"""
        if not jobs:
            return {
                'total_jobs': 0,
                'total_spent': 0,
                'avg_job_value': 0,
                'completion_rate': 0,
                'preferred_category': None
            }
            
        completed_jobs = [job for job in jobs if job.get('status') == 'completed']
        total_spent = sum(job.get('final_amount', 0) for job in completed_jobs)
        
        # Find most common category
        categories = [job.get('category') for job in jobs if job.get('category')]
        preferred_category = max(set(categories), key=categories.count) if categories else None
        
        return {
            'total_jobs': len(jobs),
            'completed_jobs': len(completed_jobs),
            'total_spent': total_spent,
            'avg_job_value': total_spent / len(completed_jobs) if completed_jobs else 0,
            'completion_rate': len(completed_jobs) / len(jobs) * 100 if jobs else 0,
            'preferred_category': preferred_category
        }
    
    def _analyze_service_preferences(self, jobs: List[Dict]) -> Dict:
        """Analyze user service preferences"""
        if not jobs:
            return {}
            
        categories = {}
        for job in jobs:
            category = job.get('category', 'Other')
            if category not in categories:
                categories[category] = {
                    'count': 0,
                    'total_spent': 0,
                    'avg_rating': 0
                }
            
            categories[category]['count'] += 1
            if job.get('status') == 'completed':
                categories[category]['total_spent'] += job.get('final_amount', 0)
                if job.get('rating'):
                    categories[category]['avg_rating'] = (
                        categories[category]['avg_rating'] + job.get('rating', 0)
                    ) / 2
        
        return categories
    
    def _calculate_satisfaction_metrics(self, reviews: List[Dict]) -> Dict:
        """Calculate user satisfaction metrics"""
        if not reviews:
            return {'avg_rating': 0, 'total_reviews': 0}
        
        ratings = [review.get('rating', 0) for review in reviews if review.get('rating')]
        
        return {
            'avg_rating': np.mean(ratings) if ratings else 0,
            'total_reviews': len(reviews),
            'positive_reviews': len([r for r in ratings if r >= 4]),
            'satisfaction_trend': 'improving'  # Would calculate trend
        }
    
    def _analyze_spending_patterns(self, jobs: List[Dict]) -> Dict:
        """Analyze user spending patterns"""
        if not jobs:
            return {}
        
        completed_jobs = [job for job in jobs if job.get('status') == 'completed']
        if not completed_jobs:
            return {}
        
        amounts = [job.get('final_amount', 0) for job in completed_jobs]
        
        return {
            'total_spent': sum(amounts),
            'avg_job_cost': np.mean(amounts),
            'median_job_cost': np.median(amounts),
            'max_job_cost': max(amounts),
            'spending_trend': 'stable'  # Would calculate actual trend
        }
    
    def _analyze_activity_patterns(self, jobs: List[Dict]) -> Dict:
        """Analyze user activity patterns"""
        if not jobs:
            return {}
        
        # Job frequency
        job_dates = [job.get('created_at') for job in jobs if job.get('created_at')]
        
        return {
            'total_jobs': len(jobs),
            'jobs_last_30_days': len([j for j in jobs if self._is_recent(j.get('created_at'), 30)]),
            'avg_jobs_per_month': len(jobs) / 12,  # Assuming 1 year of data
            'most_active_day': 'Saturday',  # Would calculate from actual data
            'preferred_time': 'Morning'  # Would calculate from actual data
        }
    
    def _generate_user_recommendations(self, jobs: List[Dict], reviews: List[Dict]) -> List[str]:
        """Generate personalized recommendations for user"""
        recommendations = []
        
        if not jobs:
            recommendations.append("Consider posting your first job to find quality service providers")
            return recommendations
        
        # Analyze patterns and suggest improvements
        completed_jobs = [job for job in jobs if job.get('status') == 'completed']
        
        if len(completed_jobs) / len(jobs) < 0.8:
            recommendations.append("Consider being more specific in job descriptions to improve completion rates")
        
        if reviews and np.mean([r.get('rating', 0) for r in reviews]) < 4.0:
            recommendations.append("Look for providers with higher ratings and more reviews")
        
        # Category-specific recommendations
        categories = [job.get('category') for job in jobs]
        if categories.count('Plumbing') > 2:
            recommendations.append("Consider preventive maintenance to reduce emergency plumbing needs")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def _is_recent(self, date_str: str, days: int) -> bool:
        """Check if a date string is within the last N days"""
        try:
            if not date_str:
                return False
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return (datetime.utcnow() - date).days <= days
        except:
            return False
    
    async def _get_user_jobs(self, user_id: str) -> List[Dict]:
        """Get user jobs (simulated for demo)"""
        # In production, this would query the database
        return [
            {
                'id': 1,
                'category': 'Plumbing',
                'status': 'completed',
                'final_amount': 450,
                'created_at': datetime.utcnow().isoformat(),
                'rating': 4.8
            },
            {
                'id': 2,
                'category': 'Electrical',
                'status': 'completed',
                'final_amount': 320,
                'created_at': (datetime.utcnow() - timedelta(days=15)).isoformat(),
                'rating': 4.5
            }
        ]
    
    async def _get_user_reviews(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get user reviews (simulated for demo)"""
        # In production, this would query the database
        return [
            {'rating': 4.8, 'created_at': datetime.utcnow().isoformat()},
            {'rating': 4.5, 'created_at': (datetime.utcnow() - timedelta(days=10)).isoformat()}
        ]


def create_data_services(app, cache_service) -> Dict[str, Any]:
    """Create and initialize data processing services"""
    try:
        # Initialize data processor
        data_processor = RealTimeDataProcessor(cache_service)
        
        # Initialize business intelligence engine
        bi_engine = MarketplaceIntelligenceEngine(cache_service)
        
        # Store services in app config
        services = {
            'data_processor': data_processor,
            'bi_engine': bi_engine,
            'cache_service': cache_service
        }
        
        logger.info("✅ Data services created successfully")
        return services
        
    except Exception as e:
        logger.error(f"❌ Error creating data services: {e}")
        return {}
