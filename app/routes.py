
import os
import uuid
from flask import Blueprint, current_app, request
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models import Document
from app.nlp import extract_keywords
from sqlalchemy import or_
from pypdf.errors import PdfReadError

documents_bp = Blueprint("documents", __name__, url_prefix="/api/documents")

ALLOWED_EXTENSIONS = {"pdf", "txt"}


@documents_bp.route("", methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return {"error": "No file provided"}, 400

    file = request.files["file"]

    if not file.filename:
        return {"error": "No file selected"}, 400

    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        return {"error": "Only PDF and TXT files are supported"}, 400

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    stored_filename = f"{uuid.uuid4().hex}.{extension}"
    file_path = os.path.join(upload_dir, stored_filename)

    try:
        file.save(file_path)

        if extension == "pdf":
            reader = PdfReader(file_path)
            if reader.is_encrypted:
                os.remove(file_path)
                return {"error": "Encrypted PDFs are not supported"}, 400
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                content = f.read()

        if not content.strip():
            os.remove(file_path)
            return {"error": "No extractable text found in the document"}, 400

        # document = Document(
        #     filename=stored_filename,
        #     original_filename=original_filename,
        #     content=content
        # )

        keywords = extract_keywords(content)

        document = Document(
            filename=stored_filename,
            original_filename=original_filename,
            content=content,
            keywords=", ".join(keywords)
        )

        db.session.add(document)
        db.session.commit()

        return {
            "message": "Document uploaded successfully",
            "document": {
                "id": document.id,
                "filename": document.original_filename,
                "characters": len(content),
                "created_at": document.created_at.isoformat()
            }
        }, 201

    except UnicodeDecodeError:
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"error": "TXT file must use UTF-8 encoding"}, 400
    except PdfReadError:
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"error": "Invalid or corrupted PDF file"}, 400
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Document upload failed")
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"error": "Document processing failed"}, 500


# @documents_bp.route("", methods=["GET"])
# def list_documents():
#     documents = Document.query.order_by(Document.created_at.desc()).all()

#     return {
#         "count": len(documents),
#         "documents": [
#             {
#                 "id": doc.id,
#                 "filename": doc.original_filename,
#                 "keywords": doc.keywords.split(", ") if doc.keywords else [],
#                 "characters": len(doc.content),
#                 "created_at": doc.created_at.isoformat()
#             }
#             for doc in documents
#         ]
#     }, 200


@documents_bp.route("", methods=["GET"])
def list_documents():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        return {"error": "page and per_page must be integers"}, 400

    if page < 1 or per_page < 1 or per_page > 100:
        return {"error": "page must be positive and per_page must be between 1 and 100"}, 400

    pagination = Document.query.order_by(
        Document.created_at.desc(), Document.id.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_documents": pagination.total,
        "total_pages": pagination.pages,
        "documents": [
            {
                "id": doc.id,
                "filename": doc.original_filename,
                "keywords": doc.keywords.split(", ") if doc.keywords else [],
                "characters": len(doc.content),
                "created_at": doc.created_at.isoformat()
            }
            for doc in pagination.items
        ]
    }, 200


@documents_bp.route("/<int:document_id>", methods=["GET"])
def get_document(document_id):
    document = db.session.get(Document, document_id)

    if document is None:
        return {"error": "Document not found"}, 404

    return {
        "id": document.id,
        "filename": document.original_filename,
        "content": document.content,
        "keywords": document.keywords.split(", ") if document.keywords else [],
        "created_at": document.created_at.isoformat()
    }, 200

# @documents_bp.route("/search", methods=["GET"])
# def search_documents():
#     query = request.args.get("q", "").strip()

#     if not query:
#         return {"error": "Search query parameter 'q' is required"}, 400

#     search_pattern = f"%{query}%"

#     documents = Document.query.filter(
#         or_(
#             Document.content.ilike(search_pattern),
#             Document.original_filename.ilike(search_pattern),
#             Document.keywords.ilike(search_pattern)
#         )
#     ).order_by(Document.created_at.desc()).all()

#     return {
#         "query": query,
#         "count": len(documents),
#         "results": [
#             {
#                 "id": doc.id,
#                 "filename": doc.original_filename,
#                 "keywords": doc.keywords.split(", ") if doc.keywords else [],
#                 "characters": len(doc.content),
#                 "created_at": doc.created_at.isoformat()
#             }
#             for doc in documents
#         ]
#     }, 200


# @documents_bp.route("/search", methods=["GET"])
# def search_documents():
#     from sqlalchemy import text

#     query = request.args.get("q", "").strip()

#     if not query:
#         return {"error": "Search query parameter 'q' is required"}, 400

#     sql = text("""
#         SELECT id
#         FROM documents
#         WHERE to_tsvector('english', content)
#               @@ plainto_tsquery('english', :query)
#            OR original_filename ILIKE :pattern
#            OR keywords ILIKE :pattern
#         ORDER BY created_at DESC
#     """)

#     rows = db.session.execute(
#         sql,
#         {"query": query, "pattern": f"%{query}%"}
#     ).fetchall()

#     documents = [
#         db.session.get(Document, row.id)
#         for row in rows
#     ]

#     return {
#         "query": query,
#         "count": len(documents),
#         "results": [
#             {
#                 "id": doc.id,
#                 "filename": doc.original_filename,
#                 "keywords": doc.keywords.split(", ") if doc.keywords else [],
#                 "characters": len(doc.content),
#                 "created_at": doc.created_at.isoformat()
#             }
#             for doc in documents
#         ]
#     }, 200


@documents_bp.route("/search", methods=["GET"])
def search_documents():
    from sqlalchemy import text

    query = request.args.get("q", "").strip()

    if not query:
        return {"error": "Search query parameter 'q' is required"}, 400

    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        return {"error": "page and per_page must be integers"}, 400

    if page < 1 or per_page < 1 or per_page > 100:
        return {"error": "page must be positive and per_page must be between 1 and 100"}, 400

    sql = text("""
        SELECT id
        FROM documents
        WHERE to_tsvector('english', content)
              @@ plainto_tsquery('english', :query)
           OR original_filename ILIKE :pattern
           OR keywords ILIKE :pattern
        ORDER BY created_at DESC, id DESC
    """)

    rows = db.session.execute(
        sql,
        {"query": query, "pattern": f"%{query}%"}
    ).fetchall()

    matching_ids = [row.id for row in rows]
    total = len(matching_ids)
    start = (page - 1) * per_page
    page_ids = matching_ids[start:start + per_page]

    documents = [
        db.session.get(Document, document_id)
        for document_id in page_ids
    ]

    return {
        "query": query,
        "page": page,
        "per_page": per_page,
        "total_documents": total,
        "total_pages": (total + per_page - 1) // per_page,
        "results": [
            {
                "id": doc.id,
                "filename": doc.original_filename,
                "keywords": doc.keywords.split(", ") if doc.keywords else [],
                "characters": len(doc.content),
                "created_at": doc.created_at.isoformat()
            }
            for doc in documents if doc is not None
        ]
    }, 200

@documents_bp.route("/<int:document_id>", methods=["PUT"])
def update_document(document_id):
    document = db.session.get(Document, document_id)

    if document is None:
        return {"error": "Document not found"}, 404

    if "file" not in request.files:
        return {"error": "Replacement file is required"}, 400

    file = request.files["file"]

    if not file.filename:
        return {"error": "No file selected"}, 400

    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        return {"error": "Only PDF and TXT files are supported"}, 400

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    stored_filename = f"{uuid.uuid4().hex}.{extension}"
    file_path = os.path.join(upload_dir, stored_filename)
    old_path = os.path.join(upload_dir, document.filename)

    try:
        file.save(file_path)

        if extension == "pdf":
            reader = PdfReader(file_path)
            if reader.is_encrypted:
                os.remove(file_path)
                return {"error": "Encrypted PDFs are not supported"}, 400
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                content = f.read()

        if not content.strip():
            os.remove(file_path)
            return {"error": "No extractable text found"}, 400

        keywords = extract_keywords(content)

        document.filename = stored_filename
        document.original_filename = original_filename
        document.content = content
        document.keywords = ", ".join(keywords)
        db.session.commit()

        if os.path.exists(old_path):
            os.remove(old_path)

        return {
            "message": "Document updated successfully",
            "id": document.id,
            "filename": document.original_filename,
            "keywords": keywords
        }, 200

    except UnicodeDecodeError:
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"error": "TXT file must use UTF-8 encoding"}, 400
    except PdfReadError:
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"error": "Invalid or corrupted PDF file"}, 400
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Document update failed")
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"error": "Document update failed"}, 500


@documents_bp.route("/<int:document_id>", methods=["DELETE"])
def delete_document(document_id):
    document = db.session.get(Document, document_id)

    if document is None:
        return {"error": "Document not found"}, 404

    file_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        document.filename
    )

    try:
        db.session.delete(document)
        db.session.commit()

        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "message": "Document deleted successfully",
            "id": document_id
        }, 200

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Document deletion failed")
        return {"error": "Document deletion failed"}, 500
