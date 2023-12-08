'''
通过txt格式载入document时，根据数据库结果增加metadata内容
调用chains.local_doc_qa.load_file读取txt变成docs，具体方法是langchain.document_loaders.text.TextLoader.load，因此实现子类功能增强
'''

import logging
import pymysql
from langchain.document_loaders import TextLoader
from typing import List, Optional
from langchain.docstore.document import Document
from langchain.document_loaders.helpers import detect_file_encodings

logger = logging.getLogger(__name__)


def set_metadata(metadata, **kwargs):
    for k, v in kwargs.items():
        if k in metadata.keys():
            metadata.update({k: v})


# Python 的模块就是天然的单例模式，因为模块在第一次导入时，会生成 .pyc 文件，
# 当第二次导入时，就会直接加载 .pyc 文件，而不会再次执行模块代码
class TextLoaderWithMoreMd(TextLoader):
    def __init__(self, file_path: str):
        super().__init__(file_path)
        host = Constants.MYSQL_HOST
        database = Constants.MYSQL_DATABASE
        user = Constants.MYSQL_USER
        password = Constants.MYSQL_PASSWORD
        self.db = pymysql.connect(host=host, user=user, password=password, database=database, charset='utf8')
        self.cursor = self.db.cursor()

    def load(self) -> List[Document]:
        """Load from file path and mysql database to get more metadata."""
        text = ""
        try:
            with open(self.file_path, encoding=self.encoding) as f:
                text = f.read()
        except UnicodeDecodeError as e:
            if self.autodetect_encoding:
                detected_encodings = detect_file_encodings(self.file_path)
                for encoding in detected_encodings:
                    logger.debug("Trying encoding: ", encoding.encoding)
                    try:
                        with open(self.file_path, encoding=encoding.encoding) as f:
                            text = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
            else:
                raise RuntimeError(f"Error loading {self.file_path}") from e
        except Exception as e:
            raise RuntimeError(f"Error loading {self.file_path}") from e

        metadata = self.get_metadata_from_mysql()
        return [Document(page_content=text, metadata=metadata)]

    def get_metadata_from_mysql(self):
        metadata = {'status': 'fail'}
        try:
            sql = ''
            self.cursor.execute(sql)
            results = self.cursor.fetchone()
            set_metadata(metadata, zhanwei=results[0], zhanwei2=results[1])
            set_metadata(metadata, status='Success')
            return metadata
        except:
            return metadata
