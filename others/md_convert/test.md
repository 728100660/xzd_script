根据dify的#12092提交进行的代码分析

# 思路
1. 从models开始看，看看数据库做了哪方面的更改
2. 从controller开始看，看对外接口做了哪方面的更改（这里新增的接口都没列出来，感兴趣可自行研究）
3. 从indexing模块开始看，看看在索引的时候有什么区别
4. 从retrieval模块开始看，看看在召回的时候做了哪些操作

# models
新增了一张child_chunks表

```python
class ChildChunk(db.Model):
    __tablename__ = "child_chunks"
    __table_args__ = (
        db.PrimaryKeyConstraint("id", name="child_chunk_pkey"),
        db.Index("child_chunk_dataset_id_idx", "tenant_id", "dataset_id", "document_id", "segment_id", "index_node_id"),
    )

    # initial fields
    id = db.Column(StringUUID, nullable=False, server_default=db.text("uuid_generate_v4()"))
    tenant_id = db.Column(StringUUID, nullable=False)
    dataset_id = db.Column(StringUUID, nullable=False)
    document_id = db.Column(StringUUID, nullable=False)
    segment_id = db.Column(StringUUID, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    word_count = db.Column(db.Integer, nullable=False)
    # indexing fields
    index_node_id = db.Column(db.String(255), nullable=True)
    index_node_hash = db.Column(db.String(255), nullable=True)
    type = db.Column(db.String(255), nullable=False, server_default=db.text("'automatic'::character varying"))
    created_by = db.Column(StringUUID, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.text("CURRENT_TIMESTAMP(0)"))
    updated_by = db.Column(StringUUID, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.text("CURRENT_TIMESTAMP(0)"))
    indexing_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    error = db.Column(db.Text, nullable=True)

    @property
    def dataset(self):
        return db.session.query(Dataset).filter(Dataset.id == self.dataset_id).first()

    @property
    def document(self):
        return db.session.query(Document).filter(Document.id == self.document_id).first()

    @property
    def segment(self):
        return db.session.query(DocumentSegment).filter(DocumentSegment.id == self.segment_id).first()



```

那么他是怎么和父分段关联起来的呢，我们继续看

在分段下面多了一个属性，child_chunks，由此可以猜测子分段是对segment进行的拆分

其实这里可以看到，FULL_DOC模式与父子模式没关系

```python
class DocumentSegment(db.Model):  # type: ignore[name-defined]

    @property
    def child_chunks(self):
        process_rule = self.document.dataset_process_rule
        if process_rule.mode == "hierarchical":
            rules = Rule(**process_rule.rules_dict)
            if rules.parent_mode and rules.parent_mode != ParentMode.FULL_DOC:
                child_chunks = (
                    db.session.query(ChildChunk)
                    .filter(ChildChunk.segment_id == self.id)
                    .order_by(ChildChunk.position.asc())
                    .all()
                )
                return child_chunks or []
            else:
                return []
        else:
            return []
```

rag中的models也有所改动，多了一个父子文档的绑定关系

```python
class ChildDocument(BaseModel):
    """Class for storing a piece of text and associated metadata."""

    page_content: str

    vector: Optional[list[float]] = None

    """Arbitrary metadata about the page content (e.g., source, relationships to other
        documents, etc.).
    """
    metadata: Optional[dict] = Field(default_factory=dict)


class Document(BaseModel):
    children: Optional[list[ChildDocument]] = None


```

# controller
这里增加了个参数，点进去看即可知道，在更新segment的时候同时更新child模块

```python
class DatasetDocumentSegmentUpdateApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    @cloud_edition_billing_resource_check("vector_space")
    def patch(self, dataset_id, document_id, segment_id):
        parser.add_argument(
            "regenerate_child_chunks", type=bool, required=False, nullable=True, default=False, location="json"
        )
        segment = SegmentService.update_segment(SegmentUpdateArgs(**args), segment, document, dataset)
```

```python
                if document.doc_form == IndexType.PARENT_CHILD_INDEX and args.regenerate_child_chunks:
                    # regenerate child chunks
                    # get embedding model instance
                    if dataset.indexing_technique == "high_quality":
                        # check embedding model setting
                        model_manager = ModelManager()

                        if dataset.embedding_model_provider:
                            embedding_model_instance = model_manager.get_model_instance(
                                tenant_id=dataset.tenant_id,
                                provider=dataset.embedding_model_provider,
                                model_type=ModelType.TEXT_EMBEDDING,
                                model=dataset.embedding_model,
                            )
                        else:
                            embedding_model_instance = model_manager.get_default_model_instance(
                                tenant_id=dataset.tenant_id,
                                model_type=ModelType.TEXT_EMBEDDING,
                            )
                    else:
                        raise ValueError("The knowledge base index technique is not high quality!")
                    # get the process rule
                    processing_rule = (
                        db.session.query(DatasetProcessRule)
                        .filter(DatasetProcessRule.id == document.dataset_process_rule_id)
                        .first()
                    )
                    VectorService.generate_child_chunks(
                        segment, document, dataset, embedding_model_instance, processing_rule, True
                    )
```

# indexing
## index_processor说明
上一个方法的输出为下一个方法的输入

extract方法提取文件内容------> transform格式化内容----->load 存储内容到向量数据库

## 内容理解说明


前面的探索发现知识更改了数据库方面的存储，看看index是做了什么吧

增加了一个processor的类，专门处理父子模式：core/rag/index_processor/processor/parent_child_index_processor.py



transform中，分别对待ParentMode.PARAGRAPH和ParentMode.FULL_DOC，

他们的区别呢就是PARAGRAPH模式是对文档进行了切分，每一个分段都切分出相应的子模块。

而FULL_DOC将全部文档作为一个上下文，所有的子块都属于一个父块

```python
def transform(self, documents: list[Document], **kwargs) -> list[Document]:
    process_rule = kwargs.get("process_rule")
    rules = Rule(**process_rule.get("rules"))
    all_documents = []
    if rules.parent_mode == ParentMode.PARAGRAPH:
        # Split the text documents into nodes.
        splitter = self._get_splitter(
            processing_rule_mode=process_rule.get("mode"),
            max_tokens=rules.segmentation.max_tokens,
            chunk_overlap=rules.segmentation.chunk_overlap,
            separator=rules.segmentation.separator,
            embedding_model_instance=kwargs.get("embedding_model_instance"),
        )
        for document in documents:
            # document clean
            document_text = CleanProcessor.clean(document.page_content, process_rule)
            document.page_content = document_text
            # parse document to nodes
            document_nodes = splitter.split_documents([document])
            split_documents = []
            for document_node in document_nodes:
                if document_node.page_content.strip():
                    doc_id = str(uuid.uuid4())
                    hash = helper.generate_text_hash(document_node.page_content)
                    document_node.metadata["doc_id"] = doc_id
                    document_node.metadata["doc_hash"] = hash
                    # delete Splitter character
                    page_content = document_node.page_content
                    if page_content.startswith(".") or page_content.startswith("。"):
                        page_content = page_content[1:].strip()
                    else:
                        page_content = page_content
                    if len(page_content) > 0:
                        document_node.page_content = page_content
                        # parse document to child nodes
                        child_nodes = self._split_child_nodes(
                            document_node, rules, process_rule.get("mode"), kwargs.get("embedding_model_instance")
                        )
                        document_node.children = child_nodes
                        split_documents.append(document_node)
            all_documents.extend(split_documents)
    elif rules.parent_mode == ParentMode.FULL_DOC:
        page_content = "\n".join([document.page_content for document in documents])
        document = Document(page_content=page_content, metadata=documents[0].metadata)
        # parse document to child nodes
        child_nodes = self._split_child_nodes(
            document, rules, process_rule.get("mode"), kwargs.get("embedding_model_instance")
        )
        document.children = child_nodes
        doc_id = str(uuid.uuid4())
        hash = helper.generate_text_hash(document.page_content)
        document.metadata["doc_id"] = doc_id
        document.metadata["doc_hash"] = hash
        all_documents.append(document)

    return all_documents
```

可以看到多了一个方法_split_child_nodes，他主要针对Document对象的pagecontent进行一个子分段拆分。

child_splitter=child_splitter = self._get_splitter(.........)，主要使用这个对分段进行拆分，拆分最大长度为rules.subchunk_segmentation.max_tokens

但这里我们能看到，其实index_processor并不会将父模块的内容存储到向量数据库中，向量数据库存储的都是child_chunk的内容

```python


def _split_child_nodes(
    self,
    document_node: Document,
    rules: Rule,
    process_rule_mode: str,
    embedding_model_instance: Optional[ModelInstance],
) -> list[ChildDocument]:
    child_splitter = self._get_splitter(
        processing_rule_mode=process_rule_mode,
        max_tokens=rules.subchunk_segmentation.max_tokens,
        chunk_overlap=rules.subchunk_segmentation.chunk_overlap,
        separator=rules.subchunk_segmentation.separator,
        embedding_model_instance=embedding_model_instance,
    )
    # parse document to child nodes
    child_nodes = []
    child_documents = child_splitter.split_documents([document_node])
    for child_document_node in child_documents:
        if child_document_node.page_content.strip():
            doc_id = str(uuid.uuid4())
            hash = helper.generate_text_hash(child_document_node.page_content)
            child_document = ChildDocument(
                page_content=child_document_node.page_content, metadata=document_node.metadata
            )
            child_document.metadata["doc_id"] = doc_id
            child_document.metadata["doc_hash"] = hash
            child_page_content = child_document.page_content
            if child_page_content.startswith(".") or child_page_content.startswith("。"):
                child_page_content = child_page_content[1:].strip()
            if len(child_page_content) > 0:
                child_document.page_content = child_page_content
                child_nodes.append(child_document)
    return child_nodes
```

# retrieval
讲完了存储，我们再来看父子模式是如何召回的吧

在：core/rag/retrieval/dataset_retrieval.py中做了下结构调整，新增了一行代码

records = RetrievalService.format_retrieval_documents(newgrand_documents)

注意，这行代码并不影响向量数据库的召回，向量数据库召回是通过single_retrieve、multiple_retrieve拿到结果的，records只是针对向量数据库召回结果进行了一个数据补充的处理

```python
    def retrieve(
        self,
        app_id: str,
        user_id: str,
        tenant_id: str,
        model_config: ModelConfigWithCredentialsEntity,
        config: DatasetEntity,
        query: str,
        invoke_from: InvokeFrom,
        show_retrieve_source: bool,
        hit_callback: DatasetIndexToolCallbackHandler,
        message_id: str,
        memory: Optional[TokenBufferMemory] = None,
    ) -> Optional[str]:
        .
        .
        
        if retrieve_config.retrieve_strategy == DatasetRetrieveConfigEntity.RetrieveStrategy.SINGLE:
            all_documents = self.single_retrieve(
                app_id,
                tenant_id,
                user_id,
                user_from,
                available_datasets,
                query,
                model_instance,
                model_config,
                planning_strategy,
                message_id,
            )
        elif retrieve_config.retrieve_strategy == DatasetRetrieveConfigEntity.RetrieveStrategy.MULTIPLE:
            all_documents = self.multiple_retrieve(
                app_id,
                tenant_id,
                user_id,
                user_from,
                available_datasets,
                query,
                retrieve_config.top_k,
                retrieve_config.score_threshold,
                retrieve_config.rerank_mode,
                retrieve_config.reranking_model,
                retrieve_config.weights,
                True if retrieve_config.reranking_enabled is None else retrieve_config.reranking_enabled,
                message_id,
            )
        .
        .
        .
        records = RetrievalService.format_retrieval_documents(newgrand_documents)
```



这段函数的主要作用是：针对向量数据库返回的child chunk，找到其对应父块的segment信息，然后将子块的分数信息赋值给父块，这样的话，最终返回的结果就是：父块上下文+子块匹配的最高分数+匹配到的子块信息

```python
@staticmethod
def format_retrieval_documents(documents: list[Document]) -> list[RetrievalSegments]:
    records = []
    include_segment_ids = []
    segment_child_map = {}
    for document in documents:
        document_id = document.metadata["document_id"]
        dataset_document = db.session.query(DatasetDocument).filter(DatasetDocument.id == document_id).first()
        if dataset_document and dataset_document.doc_form == IndexType.PARENT_CHILD_INDEX:
            child_index_node_id = document.metadata["doc_id"]
            result = (
                db.session.query(ChildChunk, DocumentSegment)
                .join(DocumentSegment, ChildChunk.segment_id == DocumentSegment.id)
                .filter(
                    ChildChunk.index_node_id == child_index_node_id,
                    DocumentSegment.dataset_id == dataset_document.dataset_id,
                    DocumentSegment.enabled == True,
                    DocumentSegment.status == "completed",
                )
                .first()
            )
            if result:
                child_chunk, segment = result
                if not segment:
                    continue
                if segment.id not in include_segment_ids:
                    include_segment_ids.append(segment.id)
                    child_chunk_detail = {
                        "id": child_chunk.id,
                        "content": child_chunk.content,
                        "position": child_chunk.position,
                        "score": document.metadata.get("score", 0.0),
                    }
                    map_detail = {
                        "max_score": document.metadata.get("score", 0.0),
                        "child_chunks": [child_chunk_detail],
                    }
                    segment_child_map[segment.id] = map_detail
                    record = {
                        "segment": segment,
                    }
                    records.append(record)
                else:
                    child_chunk_detail = {
                        "id": child_chunk.id,
                        "content": child_chunk.content,
                        "position": child_chunk.position,
                        "score": document.metadata.get("score", 0.0),
                    }
                    segment_child_map[segment.id]["child_chunks"].append(child_chunk_detail)
                    segment_child_map[segment.id]["max_score"] = max(
                        segment_child_map[segment.id]["max_score"], document.metadata.get("score", 0.0)
                    )
            else:
                continue
        else:
            index_node_id = document.metadata["doc_id"]

            segment = (
                db.session.query(DocumentSegment)
                .filter(
                    DocumentSegment.dataset_id == dataset_document.dataset_id,
                    DocumentSegment.enabled == True,
                    DocumentSegment.status == "completed",
                    DocumentSegment.index_node_id == index_node_id,
                )
                .first()
            )

            if not segment:
                continue
            include_segment_ids.append(segment.id)
            record = {
                "segment": segment,
                "score": document.metadata.get("score", None),
            }

            records.append(record)
        for record in records:
            if record["segment"].id in segment_child_map:
                record["child_chunks"] = segment_child_map[record["segment"].id].get("child_chunks", None)
                record["score"] = segment_child_map[record["segment"].id]["max_score"]

    return [RetrievalSegments(**record) for record in records]
```

# 变更对比说明
## IndexingRunner.indexing_estimate
![](https://cdn.nlark.com/yuque/0/2025/png/29307382/1748584243720-6c79d082-324f-46b6-94be-70297cdd4e5a.png)

### 1 <font style="color:#bcbec4;background-color:#1e1f22;">documents获取方式</font>
可以看到这里做了优化，之前使用的是一个通用的，需要适配多种情况，现在变为processor，不同的类型有不同的表现，符合面向对象编程的思想

![](https://cdn.nlark.com/yuque/0/2025/png/29307382/1748584449141-3a28de41-e71e-4e8d-8329-c2059321902b.png)

### 2 对于普通分段模式处理
更改了返回值，返回值部分统一处理



### 3 对于qa分段处理
可以看到处理效果是一样的，只不过是对于qa文档的处理统一放在了transform里面

![](https://cdn.nlark.com/yuque/0/2025/png/29307382/1748585366788-10cc290f-e917-431d-8466-ce38cfbb1a2d.png)

### 4 返回结构修改
注意：之前的preview_textsl里面的内容是list[str]，现在改成list[Object]了

![](https://cdn.nlark.com/yuque/0/2025/png/29307382/1748586719972-a733752e-45d9-475d-89b1-492033ba32f4.png)

## DatasetRetrieval.retrieve
### segment获取方式修改
可以看到此次更改segment的获取方式改到<font style="color:#bcbec4;background-color:#1e1f22;">RetrievalService.format_retrieval_documents</font> 里面去了，封装成一个records对象返回

![](https://cdn.nlark.com/yuque/0/2025/png/29307382/1748590731773-19c5c0aa-9156-438e-b7ff-11ab295636b4.png)

#### 非父子模式部分
没有做任何更改

![](https://cdn.nlark.com/yuque/0/2025/png/29307382/1748591006506-134eea5d-1369-4a50-9d45-78005904984f.png)

#### 父子模式
父子模式则是便利segments，为每个segments节点添加子节点信息

![](https://cdn.nlark.com/yuque/0/2025/png/29307382/1748591079271-3245dde1-23c2-43c9-b4f3-543de292278c.png)

## VectorService.create_segments_vector
![](https://cdn.nlark.com/yuque/0/2025/png/29307382/1748591740574-f6fa8a9e-ba48-4bcb-a4fa-a5ef543f8ad9.png)

# 测试计划
```python
def indexing_estimate(
        self,
        tenant_id: str,
        extract_settings: list[ExtractSetting],
        tmp_processing_rule: dict,
        doc_form: Optional[str] = None,
        doc_language: str = "English",
        dataset_id: Optional[str] = None,
        indexing_technique: str = "economy",
    ) -> IndexingEstimate:
    # 正常模式已测试
    # QA未测试


    # 检查调用传参		OK
    def _get_splitter(
        processing_rule_mode: str,
        max_tokens: int,
        chunk_overlap: int,
        separator: str,
        embedding_model_instance: Optional[ModelInstance],
    ) -> TextSplitter:
        # AUTO		测试成果
        # custom	测试通过

    # 无地方调用，不用测
    def format_split_text(text: str) -> list[QAPreviewDetail]:


    IndexingRunner._load()

    IndexingRunner._load_segments()

    # 工作流的方法，这里我还没改，测试对比下输出结果
    def _fetch_dataset_retriever(self, node_data: KnowledgeRetrievalNodeData, query: str) -> list[dict[str, Any]]:


    参数返回值未改变
    DatasetRetrieval.retrieve
    测试通过

    # 检查调用传参		OK
    BaseIndexProcessor._get_splitter

    # 检查调用传参		OK
    QAIndexProcessor.transform

    # 检查调用传参		OK
    ParagraphIndexProcessor.transform
    #默认规则	通过
    # 自定义规则	

    # 检查调用传参		OK
    ParagraphIndexProcessor.load
    #默认规则	通过

    # 改了参数     参数都加了， check
    SegmentService.update_segment

    # 改了参数     参数都加了， check
    VectorService.create_segments_vector

    # 检查调用传参		OK
    add_documents
    # 无需检查
```

1. 纯文本上传		默认规则			通过
2. 纯文本上传		自定义规则		通过
3. 文档带图片上传	默认规则			测试通过
4. 文档带图片上传	自定义规则		测试通过
5. 纯文本上传		qa模式自定义		不行，切换回原来的版本QA模式也用不了
6. 文档带图片		QA模式默认		测试结果为空？

