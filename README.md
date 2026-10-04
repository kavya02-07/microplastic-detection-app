# Clarium — AI-Powered Microplastic Detection and Analysis

Clarium is an AI-powered web application for detecting, classifying, and quantitatively analyzing microplastic particles in aquatic sample images.

The system uses a YOLOv8-based object detection model to identify four morphological classes of microplastics:

- Fibers
- Films
- Fragments
- Pellets

Clarium combines AI-based detection with particle-level measurements, analysis history, visualization, model evaluation, authentication, and automated PDF reporting in a full-stack application.

---

## Key Features

### AI-Based Detection
- YOLOv8 Medium object detection model
- Detection of four microplastic morphological classes
- Adjustable confidence threshold
- Bounding-box visualization
- Particle-level confidence scores

### Quantitative Analysis
For every detected particle, Clarium calculates:

- Bounding-box width
- Bounding-box height
- Bounding-box area
- Aspect ratio
- Confidence score
- Class distribution


### Analysis History
- Persistent analysis records
- User-specific history
- Detailed historical analysis
- Stored particle-level detection data
- No need to rerun the model to view previous analyses

### Authentication
- User registration and login
- Password hashing using bcrypt
- JWT-based authentication
- Protected API routes
- User-level data isolation

### Reports and Visualization
Clarium can generate PDF analysis reports containing:

- Morphology composition
- Class distribution
- Confidence distribution
- Particle-area distribution
- Class-wise particle-area analysis
- Detection-density visualization
- Confidence vs. particle-area analysis
- Model evaluation information
- Scientific interpretation and limitations


---


 

