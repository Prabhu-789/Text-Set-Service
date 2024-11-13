# # upload_service.py

# from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, APIRouter
# import pandas as pd
# import numpy as np
# from io import BytesIO
# from sqlalchemy import text
# from sentence_transformers import SentenceTransformer
# from controller import oauth2_scheme
# from sqlalchemy.orm import Session
# from controller import authenticate_user
# from database import get_db
# import logging
# import os
# from datetime import datetime
# from dateutil import parser # type: ignore
# from uuid import uuid4

# # Logging setup
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # FastAPI app
# route = APIRouter()

# # Sentence Transformer model
# model = SentenceTransformer('all-MiniLM-L6-v2')
# tokenizer = model.tokenizer

# # Mandatory columns based on the database table structure
# mandatory_columns = ['creator_id', 'creator_name', 'text_content', 'post_date', 'external_item_id', 'parent_external_item_id', 'text_item_id']

# # Function to parse ISO 8601 date format
# def parse_iso8601_date(date_str):
#     try:
#         return parser.isoparse(date_str)
#     except Exception as e:
#         logger.error(f"Error parsing date {date_str}: {e}")
#         return None

# # Function to split long text into segments
# def segment_text(text, max_length=300, overlap=50):
#     tokens = tokenizer.tokenize(text)
#     segments = []
#     for i in range(0, len(tokens), max_length - overlap):
#         segment_tokens = tokens[i:i + max_length]
#         segment = tokenizer.convert_tokens_to_string(segment_tokens)
#         segments.append(segment)
#     return segments

# # Upload file endpoint
# @route.post("TextSet/{text_set_id}/upload-file/")
# async def upload_file(
#     file: UploadFile = File(...),
#     token: str = Depends(oauth2_scheme),
#     db: Session = Depends(get_db)
# ):
#     # Verify the user token and get user_id
#     user_id = authenticate_user(token, db)

#     try:
#         contents = await file.read()
#         df = pd.read_excel(BytesIO(contents))

#         # Ensure mandatory columns are present
#         missing_columns = [col for col in mandatory_columns if col not in df.columns]
#         if missing_columns:
#             raise HTTPException(status_code=400, detail=f"Missing mandatory columns: {missing_columns}")

#         # Process the DataFrame and store data in the database
#         with db.begin():  # Use transaction
#             for _, row in df.iterrows():
#                 if pd.isnull(row['text_content']):
#                     logger.warning("Missing 'text_content' in the row. Skipping...")
#                     continue

#                 # Process text segments
#                 text_content = row['text_content']
#                 segments = segment_text(text_content)

#                 # Parse post date
#                 post_date = parse_iso8601_date(row['post_date'])
#                 if not post_date:
#                     raise HTTPException(status_code=400, detail=f"Invalid date format for 'post_date': {row['post_date']}")

#                 for i, segment in enumerate(segments):
#                     # Generate embeddings for the segment
#                     embedding = model.encode(segment)
#                     embedding_array = np.array(embedding, dtype=np.float32)

#                     # Set parameters for insertion
#                     params = {
#                         'creator_id': row['creator_id'],
#                         'creator_name': row['creator_name'],
#                         'text_set_id': row.get('text_set_id'),
#                         'text_item_id': str(uuid4()),
#                         'text_content': segment,
#                         'post_date': post_date,
#                         'external_item_id': row.get('external_item_id'),
#                         'parent_external_item_id': row.get('parent_external_item_id'),
#                         'embeddings': embedding_array.tolist()
#                     }

#                     try:
#                         column_names = ', '.join(params.keys())
#                         placeholders = ', '.join([f":{key}" for key in params.keys()])
#                         insert_query = text(f"""
#                             INSERT INTO TextItem ({column_names})
#                             VALUES ({placeholders})
#                         """)

#                         db.execute(insert_query, params)
#                         logger.info(f"Segment {i} for Creator ID {row['creator_id']} inserted successfully.")

#                     except Exception as e:
#                         db.rollback()
#                         logger.error(f"Error inserting segment {i} for Creator ID {row['creator_id']}: {e}")
#                         raise HTTPException(status_code=500, detail=f"Error inserting segment {i} for Creator ID {row['creator_id']}")

#         return {"message": "File processed and data inserted successfully"}

#     except Exception as e:
#         logger.error(f"Error processing file: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
# upload_service.py

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, APIRouter, Path
import pandas as pd
import numpy as np
from io import BytesIO
from sqlalchemy import text
from sentence_transformers import SentenceTransformer
from controller import oauth2_scheme
from sqlalchemy.orm import Session
from controller import authenticate_user
from database import get_db
from models import TextSet
import logging
from uuid import uuid4
from datetime import datetime
from dateutil import parser  # type: ignore

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI router
route = APIRouter()

# Sentence Transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')
tokenizer = model.tokenizer

# Mandatory columns based on the database table structure
mandatory_columns = ['creator_id', 'creator_name', 'text_content', 'post_date', 'external_item_id', 'parent_external_item_id']

# Function to parse ISO 8601 date format
def parse_iso8601_date(date_str):
    try:
        return parser.isoparse(date_str)
    except Exception as e:
        logger.error(f"Error parsing date {date_str}: {e}")
        return None

# Function to split long text into segments
def segment_text(text, max_length=300, overlap=50):
    tokens = tokenizer.tokenize(text)
    segments = []
    for i in range(0, len(tokens), max_length - overlap):
        segment_tokens = tokens[i:i + max_length]
        segment = tokenizer.convert_tokens_to_string(segment_tokens)
        segments.append(segment)
    return segments

# Upload file endpoint with text_set_id path parameter
@route.post("/TextSet/{text_set_id}/upload-file/")
@route.post("/TextSet/{text_set_id}/upload-file/")
async def upload_file(
    text_set_id: str = Path(..., description="UUID of the TextSet to associate with the file"),
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    valid_extensions = ['.xls', '.xlsx']
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in valid_extensions:
        raise HTTPException(status_code=400, detail="Invalid file extension. Only .xls and .xlsx files are allowed.")
   
    if not (file.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" or file.content_type == "application/vnd.ms-excel"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only Excel files are allowed.")
    # Verify the user token and get user_id
    user_id = authenticate_user(token, db)

    # Check if the provided text_set_id exists in the TextSet table
    text_set = db.query(TextSet).filter_by(id=text_set_id, owner_id=user_id).first()
    if not text_set:
        raise HTTPException(status_code=404, detail="TextSet not found or not accessible")

    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))

        # Ensure mandatory columns are present in the file
        missing_columns = [col for col in mandatory_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(status_code=400, detail=f"Missing mandatory columns: {missing_columns}")

        # Process the DataFrame and store data in the database
        for _, row in df.iterrows():
            if pd.isnull(row['text_content']):
                logger.warning("Missing 'text_content' in the row. Skipping...")
                continue

            # Process text segments
            text_content = row['text_content']
            segments = segment_text(text_content)

            # Parse post date
            post_date = parse_iso8601_date(row['post_date'])
            if not post_date:
                raise HTTPException(status_code=400, detail=f"Invalid date format for 'post_date': {row['post_date']}")

            for i, segment in enumerate(segments):
                # Generate embeddings for the segment
                embedding = model.encode(segment)
                embedding_array = np.array(embedding, dtype=np.float32)

                # Set parameters for insertion
                params = {
                    'creator_id': row['creator_id'],
                    'creator_name': row['creator_name'],
                    'text_set_id': text_set_id,  # Use the path parameter
                    'text_item_id': str(uuid4()),  # Generate a new UUID for each record
                    'text_content': segment,
                    'post_date': post_date,
                    'external_item_id': row.get('external_item_id'),
                    'parent_external_item_id': row.get('parent_external_item_id'),
                    'embeddings': embedding_array.tolist()
                }

                try:
                    column_names = ', '.join(params.keys())
                    placeholders = ', '.join([f":{key}" for key in params.keys()])
                    insert_query = text(f"""
                        INSERT INTO TextItem ({column_names})
                        VALUES ({placeholders})
                    """)

                    db.execute(insert_query, params)
                    logger.info(f"Segment {i} for Creator ID {row['creator_id']} inserted successfully.")

                except Exception as e:
                    db.rollback()
                    logger.error(f"Error inserting segment {i} for Creator ID {row['creator_id']}: {e}")
                    raise HTTPException(status_code=500, detail=f"Error inserting segment {i} for Creator ID {row['creator_id']}")

        db.commit()  # Commit after processing all records

        return {"message": "File processed and data inserted successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))