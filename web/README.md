# Career Application Agent - Web Interface

A modern web interface for the Career Application Agent, providing an intuitive UI for managing your career database, analyzing job opportunities, and generating tailored application documents.

## Features

### 🎯 Dashboard
- Overview of career database status
- Recent activity tracking
- Quick action buttons
- Real-time statistics

### 📊 Career Database Management
- Build database from documents
- View and edit experiences
- Drag-and-drop file upload
- YAML editor with syntax highlighting
- Export capabilities

### 💼 Job Analysis
- Analyze job postings by URL
- Technical and cultural fit scoring
- Visual fit score representation
- Key strengths and gaps identification
- Personalized recommendations

### 📄 Document Generation
- Generate tailored CVs and cover letters
- Multiple templates and tones
- Real-time preview
- Document history
- Download options

### 📈 Workflow Tracking
- Real-time progress updates
- Workflow history
- Status filtering
- Detailed logs

## Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework
- **Uvicorn**: ASGI server
- **WebSockets**: Real-time updates
- **Pydantic**: Data validation

### Frontend
- **React 18**: UI library
- **TypeScript**: Type safety
- **Material-UI**: Component library
- **React Query**: Data fetching
- **Redux Toolkit**: State management
- **Socket.io**: WebSocket client

## Installation

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker (optional)

### Backend Setup

```bash
cd web/backend
pip install -r requirements.txt
pip install fastapi uvicorn python-multipart websockets
```

### Frontend Setup

```bash
cd web/frontend
npm install
```

## Development

### Run Backend

```bash
cd web/backend
uvicorn main:app --reload --port 8000
```

### Run Frontend

```bash
cd web/frontend
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Production Deployment

### Using Docker Compose

```bash
cd web
docker-compose up -d
```

This will start:
- Backend API on port 8000
- Frontend on port 3000
- Nginx proxy on port 80

### Environment Variables

Create a `.env` file in the web directory:

```env
OPENROUTER_API_KEY=your_api_key_here
REACT_APP_API_URL=http://localhost:8000
```

### Building for Production

#### Backend
```bash
docker build -f backend/Dockerfile -t career-agent-backend ..
```

#### Frontend
```bash
cd frontend
npm run build
docker build -t career-agent-frontend .
```

## API Documentation

FastAPI automatically generates API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

- `GET /api/health` - Health check
- `GET /api/database` - Get career database
- `POST /api/database/build` - Build career database
- `POST /api/jobs/analyze` - Analyze job posting
- `POST /api/documents/generate` - Generate documents
- `GET /api/workflows` - List workflows
- `WS /ws/workflows/{id}` - WebSocket for workflow updates

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   React Frontend    │────▶│   FastAPI Backend   │
│  - Material-UI      │     │  - WebSocket server │
│  - React Query      │     │  - Async handlers   │
│  - TypeScript       │     │  - File management  │
└─────────────────────┘     └──────────┬──────────┘
                                       │
                            ┌──────────▼──────────┐
                            │  Career Agent Core  │
                            │  - Nodes & Flows    │
                            │  - LLM Integration  │
                            └─────────────────────┘
```

## Security Considerations

1. **Authentication**: Currently not implemented (TODO)
2. **File Upload**: Validates file types
3. **CORS**: Configured for local development
4. **Input Validation**: Pydantic models
5. **Error Handling**: Comprehensive error responses

## Future Enhancements

- [ ] User authentication and authorization
- [ ] Multi-user support with isolated databases
- [ ] Email notifications for completed workflows
- [ ] Advanced search and filtering
- [ ] Batch operations
- [ ] Mobile responsive improvements
- [ ] Dark mode support
- [ ] Internationalization

## Troubleshooting

### Common Issues

1. **CORS Errors**: Check CORS configuration in `main.py`
2. **WebSocket Connection Failed**: Ensure backend is running
3. **File Upload Failed**: Check file size limits and permissions
4. **Build Errors**: Clear node_modules and reinstall

### Debug Mode

Enable debug logging:

```python
# Backend
logging.basicConfig(level=logging.DEBUG)

# Frontend
localStorage.setItem('debug', 'career-agent:*')
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

Same as parent project