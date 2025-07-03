import React, { useState, useEffect } from 'react';
import './TradesMarketplace.css';

// Sample data moved outside component to avoid dependency issues
const sampleJobs = [
  {
    id: 1,
    title: "Kitchen Renovation - Full Remodel",
    description: "Looking for experienced tradies to completely renovate my kitchen. Includes plumbing, electrical, tiling, and carpentry work.",
    location: "Sydney, NSW",
    budget: "$15,000 - $25,000",
    category: "Renovation",
    postedDate: "2 hours ago",
    quotes: 8,
    urgent: true
  },
  {
    id: 2,
    title: "Bathroom Leak Repair - Urgent",
    description: "Urgent repair needed for bathroom leak. Water damage visible on ceiling below.",
    location: "Melbourne, VIC",
    budget: "$500 - $1,500",
    category: "Plumbing",
    postedDate: "4 hours ago",
    quotes: 12,
    urgent: true
  },
  {
    id: 3,
    title: "Deck Construction - Outdoor Entertainment Area",
    description: "Build new timber deck 6m x 4m with pergola. Materials to be quoted separately.",
    location: "Brisbane, QLD",
    budget: "$8,000 - $12,000",
    category: "Carpentry",
    postedDate: "1 day ago",
    quotes: 5,
    urgent: false
  },
  {
    id: 4,
    title: "Electrical Safety Inspection",
    description: "Annual electrical safety inspection for rental property. Certificate required.",
    location: "Perth, WA",
    budget: "$200 - $400",
    category: "Electrical",
    postedDate: "2 days ago",
    quotes: 15,
    urgent: false
  }
];

const sampleProviders = [
  {
    id: 1,
    name: "Mike's Premium Plumbing",
    rating: 4.9,
    reviews: 127,
    specialties: ["Plumbing", "Gas Fitting", "Drainage"],
    location: "Sydney, NSW",
    responseTime: "Usually responds within 2 hours",
    verified: true
  },
  {
    id: 2,
    name: "Elite Electrical Services",
    rating: 4.8,
    reviews: 89,
    specialties: ["Electrical", "Solar Installation", "Home Automation"],
    location: "Melbourne, VIC",
    responseTime: "Usually responds within 1 hour",
    verified: true
  },
  {
    id: 3,
    name: "Precision Carpentry Co.",
    rating: 4.7,
    reviews: 156,
    specialties: ["Carpentry", "Renovation", "Custom Furniture"],
    location: "Brisbane, QLD",
    responseTime: "Usually responds within 4 hours",
    verified: true
  }
];

const serviceCategories = [
  { name: "Plumbing", icon: "🔧", jobs: 247 },
  { name: "Electrical", icon: "⚡", jobs: 189 },
  { name: "Carpentry", icon: "🔨", jobs: 156 },
  { name: "Painting", icon: "🎨", jobs: 134 },
  { name: "Landscaping", icon: "🌿", jobs: 87 },
  { name: "Cleaning", icon: "🧽", jobs: 76 },
];

const TradesMarketplace = () => {
  const [activeTab, setActiveTab] = useState('browse');
  const [jobs, setJobs] = useState([]);
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch jobs and providers from API
    const fetchJobs = async () => {
      try {
        const response = await fetch('/api/jobs');
        if (response.ok) {
          const data = await response.json();
          setJobs(data.jobs || []);
        }
      } catch (error) {
        console.error('Error fetching jobs:', error);
        // Fallback to sample data
        setJobs(sampleJobs);
      }
      setLoading(false);
    };

    const fetchProviders = async () => {
      try {
        const response = await fetch('/api/providers');
        if (response.ok) {
          const data = await response.json();
          setProviders(data.providers || []);
        }
      } catch (error) {
        console.error('Error fetching providers:', error);
        // Fallback to sample data
        setProviders(sampleProviders);
      }
    };

    fetchJobs();
    fetchProviders();
  }, []);

  return (
    <div className="trades-marketplace">
      {/* Header */}
      <header className="marketplace-header">
        <div className="header-content">
          <h1>🔨 Biped Trades Marketplace</h1>
          <p>Connect with trusted local tradies for all your home and business needs</p>
          
          <div className="header-actions">
            <button className="btn-primary">Post a Job</button>
            <button className="btn-secondary">Join as Tradie</button>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="marketplace-nav">
        <button 
          className={`nav-tab ${activeTab === 'browse' ? 'active' : ''}`}
          onClick={() => setActiveTab('browse')}
        >
          Browse Jobs
        </button>
        <button 
          className={`nav-tab ${activeTab === 'providers' ? 'active' : ''}`}
          onClick={() => setActiveTab('providers')}
        >
          Find Tradies
        </button>
        <button 
          className={`nav-tab ${activeTab === 'categories' ? 'active' : ''}`}
          onClick={() => setActiveTab('categories')}
        >
          Categories
        </button>
      </nav>

      {/* Main Content */}
      <main className="marketplace-content">
        {loading ? (
          <div className="loading-container">
            <p>Loading marketplace data...</p>
          </div>
        ) : (
          <>
        {activeTab === 'browse' && (
          <div className="jobs-section">
            <div className="section-header">
              <h2>Latest Jobs</h2>
              <div className="filters">
                <select>
                  <option>All Categories</option>
                  <option>Plumbing</option>
                  <option>Electrical</option>
                  <option>Carpentry</option>
                </select>
                <select>
                  <option>All Locations</option>
                  <option>Sydney, NSW</option>
                  <option>Melbourne, VIC</option>
                  <option>Brisbane, QLD</option>
                </select>
              </div>
            </div>

            <div className="jobs-grid">
              {jobs.map(job => (
                <div key={job.id} className={`job-card ${job.urgent ? 'urgent' : ''}`}>
                  {job.urgent && <span className="urgent-badge">URGENT</span>}
                  
                  <div className="job-header">
                    <h3>{job.title}</h3>
                    <span className="job-category">{job.category}</span>
                  </div>
                  
                  <p className="job-description">{job.description}</p>
                  
                  <div className="job-details">
                    <div className="job-location">📍 {job.location}</div>
                    <div className="job-budget">💰 {job.budget}</div>
                  </div>
                  
                  <div className="job-footer">
                    <span className="job-posted">{job.postedDate}</span>
                    <span className="job-quotes">{job.quotes} quotes</span>
                    <button className="btn-quote">Send Quote</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'providers' && (
          <div className="providers-section">
            <div className="section-header">
              <h2>Top Rated Tradies</h2>
              <div className="filters">
                <input type="text" placeholder="Search by name or specialty..." />
                <select>
                  <option>All Specialties</option>
                  <option>Plumbing</option>
                  <option>Electrical</option>
                  <option>Carpentry</option>
                </select>
              </div>
            </div>

            <div className="providers-grid">
              {providers.map(provider => (
                <div key={provider.id} className="provider-card">
                  <div className="provider-header">
                    <h3>{provider.name}</h3>
                    {provider.verified && <span className="verified-badge">✓ Verified</span>}
                  </div>
                  
                  <div className="provider-rating">
                    <span className="rating">⭐ {provider.rating}</span>
                    <span className="reviews">({provider.reviews} reviews)</span>
                  </div>
                  
                  <div className="provider-specialties">
                    {provider.specialties.map(specialty => (
                      <span key={specialty} className="specialty-tag">{specialty}</span>
                    ))}
                  </div>
                  
                  <div className="provider-details">
                    <div>📍 {provider.location}</div>
                    <div>✅ {provider.completedJobs} jobs completed</div>
                    <div>⏱️ {provider.responseTime}</div>
                  </div>
                  
                  <div className="provider-actions">
                    <button className="btn-primary">View Profile</button>
                    <button className="btn-secondary">Send Message</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'categories' && (
          <div className="categories-section">
            <div className="section-header">
              <h2>Service Categories</h2>
              <p>Find the right tradie for your specific needs</p>
            </div>

            <div className="categories-grid">
              {serviceCategories.map(category => (
                <div key={category.name} className="category-card">
                  <div className="category-icon">{category.icon}</div>
                  <h3>{category.name}</h3>
                  <p>{category.jobs} active jobs</p>
                  <button className="btn-category">Browse Jobs</button>
                </div>
              ))}
            </div>
          </div>
        )}
          </>
        )}
      </main>

      {/* Stats Section */}
      <section className="marketplace-stats">
        <div className="stats-container">
          <div className="stat-item">
            <h3>2,847</h3>
            <p>Active Jobs</p>
          </div>
          <div className="stat-item">
            <h3>1,256</h3>
            <p>Verified Tradies</p>
          </div>
          <div className="stat-item">
            <h3>15,432</h3>
            <p>Jobs Completed</p>
          </div>
          <div className="stat-item">
            <h3>4.8★</h3>
            <p>Average Rating</p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default TradesMarketplace;

