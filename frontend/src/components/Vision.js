import React, { useState, useEffect } from 'react';

function Vision() {
  const [visionStatus, setVisionStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch vision status
    fetch('/api/vision/status')
      .then(response => response.json())
      .then(data => {
        setVisionStatus(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching vision status:', error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="card">
        <h2>👁️ Computer Vision</h2>
        <div className="loading-spinner"></div>
        <p>Loading computer vision status...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <h2>👁️ Computer Vision Engine</h2>
        <p>AI-powered image analysis and quality control</p>
        
        <div className="grid">
          <div className="metric-card">
            <div className="metric-value">
              {visionStatus?.computer_vision?.computer_vision_available ? '✅' : '⚠️'}
            </div>
            <div className="metric-label">CV Available</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-value">OpenCV</div>
            <div className="metric-label">Engine</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-value">Headless</div>
            <div className="metric-label">Mode</div>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>🔧 Vision Capabilities</h3>
        <div className="grid">
          <div className="metric-card">
            <h4>Image Analysis</h4>
            <p>Quality assessment and defect detection</p>
            <div className="metric-value">
              {visionStatus?.computer_vision?.features?.image_analysis || 'Available'}
            </div>
          </div>
          
          <div className="metric-card">
            <h4>Progress Comparison</h4>
            <p>Before/after analysis and progress tracking</p>
            <div className="metric-value">
              {visionStatus?.computer_vision?.features?.progress_comparison || 'Available'}
            </div>
          </div>
          
          <div className="metric-card">
            <h4>Quality Assessment</h4>
            <p>Professional quality scoring</p>
            <div className="metric-value">
              {visionStatus?.computer_vision?.features?.quality_assessment || 'Available'}
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>📋 System Status</h3>
        {visionStatus?.detailed_status && (
          <div className="grid">
            <div className="metric-card">
              <h4>OpenCV</h4>
              <div className="metric-value">
                {visionStatus.detailed_status.libraries?.opencv?.available ? '✅' : '❌'}
              </div>
              <div className="metric-label">
                {visionStatus.detailed_status.libraries?.opencv?.version || 'Not available'}
              </div>
            </div>
            
            <div className="metric-card">
              <h4>PIL/Pillow</h4>
              <div className="metric-value">
                {visionStatus.detailed_status.libraries?.pillow?.available ? '✅' : '❌'}
              </div>
              <div className="metric-label">
                {visionStatus.detailed_status.libraries?.pillow?.version || 'Not available'}
              </div>
            </div>
            
            <div className="metric-card">
              <h4>NumPy</h4>
              <div className="metric-value">
                {visionStatus.detailed_status.libraries?.numpy?.available ? '✅' : '❌'}
              </div>
              <div className="metric-label">
                {visionStatus.detailed_status.libraries?.numpy?.version || 'Not available'}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="card">
        <h3>🚀 API Endpoints</h3>
        <div className="grid">
          <div className="metric-card">
            <h4>Vision Status</h4>
            <button className="btn btn-primary" onClick={() => window.open('/api/vision/status', '_blank')}>
              Check Status
            </button>
          </div>
          
          <div className="metric-card">
            <h4>Health Check</h4>
            <button className="btn btn-success" onClick={() => window.open('/api/vision/health', '_blank')}>
              Health Check
            </button>
          </div>
          
          <div className="metric-card">
            <h4>Image Analysis</h4>
            <button className="btn btn-warning" onClick={() => alert('Use POST /api/vision/analyze-image with image data')}>
              API Info
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Vision;

