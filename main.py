from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
from pathlib import Path

app = FastAPI(title="RAG Service")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建必要的目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 挂载静态文件目录（支持热更新）
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


@app.get("/")
async def root():
    """返回首页"""
    return FileResponse("static/index.html")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件接口，支持文本、PDF、Word 和 Excel"""
    print(f"收到文件上传请求: {file.filename}, 类型: {file.content_type}")
    
    # 检查文件类型
    allowed_extensions = {'.txt', '.md', '.csv', '.pdf', '.doc', '.docx', '.xls', '.xlsx'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。仅支持: {', '.join(allowed_extensions)}"
        )
    
    # 保存文件
    file_path = UPLOAD_DIR / file.filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 如果是文本文件，读取内容
        content = None
        if file_ext in {'.txt', '.md', '.csv'}:
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'iso-8859-1', 'latin-1']
            for encoding in encodings:
                try:
                    with file_path.open("r", encoding=encoding) as f:
                        content = f.read()
                    print(f"使用 {encoding} 编码成功读取文件")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"使用 {encoding} 编码读取失败: {str(e)}")
                    continue
            
            if content is None:
                print(f"无法读取文件内容，尝试的编码: {encodings}")
        
        elif file_ext == '.pdf':
            # 提取 PDF 文本内容
            try:
                import PyPDF2
                with file_path.open("rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    text_content = []
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
                    content = '\n'.join(text_content)
                    print(f"成功提取 PDF 文本内容，共 {len(reader.pages)} 页")
            except ImportError:
                print("未安装 PyPDF2，无法提取 PDF 内容")
                content = "PDF 文件已上传，但无法提取文本内容（需要安装 PyPDF2）"
            except Exception as e:
                print(f"提取 PDF 内容失败: {str(e)}")
                content = f"PDF 文件已上传，但提取文本内容失败: {str(e)}"
        
        elif file_ext in {'.doc', '.docx'}:
            # 提取 Word 文本内容
            try:
                from docx import Document
                doc = Document(file_path)
                paragraphs = []
                for para in doc.paragraphs:
                    if para.text.strip():
                        paragraphs.append(para.text)
                content = '\n'.join(paragraphs)
                print(f"成功提取 Word 文本内容")
            except ImportError:
                print("未安装 python-docx，无法提取 Word 内容")
                content = "Word 文件已上传，但无法提取文本内容（需要安装 python-docx）"
            except Exception as e:
                print(f"提取 Word 内容失败: {str(e)}")
                content = f"Word 文件已上传，但提取文本内容失败: {str(e)}"
        
        elif file_ext in {'.xls', '.xlsx'}:
            # 提取 Excel 文本内容
            try:
                import pandas as pd
                df = pd.read_excel(file_path)
                content = df.to_string(index=False)
                print(f"成功提取 Excel 文本内容")
            except ImportError:
                print("未安装 pandas 或 openpyxl，无法提取 Excel 内容")
                content = "Excel 文件已上传，但无法提取文本内容（需要安装 pandas）"
            except Exception as e:
                print(f"提取 Excel 内容失败: {str(e)}")
                content = f"Excel 文件已上传，但提取文本内容失败: {str(e)}"
        
        print(f"文件上传成功: {file.filename}, 大小: {file_path.stat().st_size}")
        
        return JSONResponse({
            "message": "文件上传成功",
            "filename": file.filename,
            "file_type": file_ext,
            "content": content,
            "size": file_path.stat().st_size
        })
    except Exception as e:
        print(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@app.post("/chat")
async def chat(message: dict):
    """聊天接口"""
    user_message = message.get("message", "")
    
    # 这里可以集成你的 RAG 逻辑
    # 目前返回一个简单的响应
    response = {
        "message": f"收到你的消息: {user_message}",
        "timestamp": "2026-01-06"
    }
    
    return JSONResponse(response)


@app.get("/uploads")
async def list_uploads():
    """获取已上传的文件列表"""
    files = []
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            files.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "type": file_path.suffix
            })
    return JSONResponse({"files": files})


@app.delete("/uploads/{filename}")
async def delete_file(filename: str):
    """删除指定文件"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail=f"不是文件: {filename}")
    
    try:
        file_path.unlink()
        print(f"文件删除成功: {filename}")
        return JSONResponse({
            "message": "文件删除成功",
            "filename": filename
        })
    except Exception as e:
        print(f"文件删除失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件删除失败: {str(e)}")


@app.post("/uploads/delete")
async def delete_files(request: dict):
    """批量删除文件"""
    filenames = request.get("filenames", [])
    
    if not filenames:
        raise HTTPException(status_code=400, detail="未指定要删除的文件")
    
    deleted = []
    failed = []
    
    for filename in filenames:
        file_path = UPLOAD_DIR / filename
        try:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                deleted.append(filename)
                print(f"文件删除成功: {filename}")
            else:
                failed.append(filename)
        except Exception as e:
            failed.append(filename)
            print(f"文件删除失败: {filename}, 错误: {str(e)}")
    
    return JSONResponse({
        "message": f"成功删除 {len(deleted)} 个文件",
        "deleted": deleted,
        "failed": failed
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000,
        reload=True,
        reload_dirs=["static"]
    )