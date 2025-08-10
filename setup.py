from setuptools import setup, find_packages

setup(
    name="document-search",
    version="1.0.0",
    description="Document search application for cloud storage services",
    author="Narendra Kumar",
    packages=find_packages(),
    install_requires=[
        "google-api-python-client==2.108.0",
        "google-auth-httplib2==0.1.1",
        "google-auth-oauthlib==1.1.0",
        "elasticsearch==8.11.0",
        "PyPDF2==3.0.1",
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "python-multipart==0.0.6",
        "requests==2.31.0",
        "python-dotenv==1.0.0",
    ],
    python_requires=">=3.8",
)