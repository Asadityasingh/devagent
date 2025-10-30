# tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint returns correct response"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_api_status():
    """Test API status endpoint"""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert "api" in data
    assert data["api"] == "operational"
