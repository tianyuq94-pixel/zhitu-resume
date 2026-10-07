import { locale } from '@/i18n'

export type Copy = { en: string; zh: string }
export const bi = (en: string, zh: string): Copy => ({ en, zh })
export const l = (text: Copy) => text[locale.value]
export const say = (en: string, zh: string) => locale.value === 'zh' ? zh : en
export const repository = 'https://github.com/tianyuq94-pixel/zhitu-resume'
export const email = 'dvwaefu7708@163.com'

export const contribution = [
  { title: bi('Defined the product', '定义产品方向'), text: bi('I set the requirements and priorities, from role-specific CVs to a single task that delivers three useful outcomes.', '我提出需求并确定优先级，从岗位定制简历逐步推进到一次任务交付三类成果。') },
  { title: bi('Turned feedback into decisions', '用实际反馈推动决策'), text: bi('Through hands-on trials, I identified near-identical rewrites, cramped results and unnecessary interview steps, then specified how the experience should change.', '通过亲自试用，我指出几乎相同的改写、结果区过小、自动面试耗时等问题，并明确提出调整方向。') },
  { title: bi('Drove iteration and delivery', '推动迭代与交付'), text: bi('I reviewed successive versions, supplied a CV template, requested editable exports and coordinated the move from local trials to a public website.', '我检查迭代版本、提供简历模板、提出可编辑导出需求，并配合完成从本地试用到公开网站的交付。') },
]

export const projects = [
  {
    id: 'career-agent', number: '01', name: bi('Career Agent', '求职智能体'), accent: 'sage', route: '/agent', image: bi('/portfolio/agent.png', '/portfolio/agent-zh.png'),
    purpose: bi('Prepare for a target role', '围绕目标岗位，准备求职'),
    enter: bi('Start a career task', '开始求职任务'),
    tag: bi('Tool calling · Stateful workflow', '工具调用 · 有状态工作流'),
    summary: bi('A CV and a target role become a guided workflow: role analysis, a tailored CV and an interview preparation plan.', '从简历和目标岗位出发，完成岗位分析、定制简历与面试准备方案。'),
    question: bi('How can an AI application carry a goal through several reliable, reviewable steps?', '如何让 AI 应用通过可靠、可检查的多个步骤完成一个目标？'),
    problem: bi('Separate tools leave users to move information between pages and decide what to do next. I wanted one goal-led task with useful outputs, without forcing a long mock interview.', '独立工具需要用户在不同页面搬运信息、安排下一步。我希望以一个目标组织任务并交付成果，同时不强迫用户开始耗时较长的模拟面试。'),
    owned: bi('I proposed the goal-based Agent, specified role and company inputs, prioritised results over process messages, and required interview preparation before an optional simulation.', '我提出目标驱动的 Agent 形式，确定岗位和公司的输入规则，要求成果优先展示，并决定先生成面试准备方案、最后再由用户选择模拟面试。'),
    steps: [bi('Confirm CV + target role', '确认简历与目标岗位'), bi('Select an allowed tool', '选择允许调用的工具'), bi('Validate + save outcome', '校验并保存成果'), bi('Continue or ask the user', '继续执行或询问用户')],
    mechanisms: [
      { title: bi('Constrained tool selection', '有约束的工具选择'), text: bi('The model chooses from job analysis, CV tailoring, preparation, asking the user and finishing. The server enforces dependencies and validates tool names and arguments.', '模型可选择岗位分析、简历定制、面试准备、询问用户或结束任务。服务端限制步骤依赖，并校验工具名称与参数。') },
      { title: bi('Saved task state', '持久化任务状态'), text: bi('Each outcome is saved before the next step. Revision checks prevent concurrent execution of the same task version; failed steps can be retried.', '每步结果保存后再进入下一步；版本检查防止同一任务版本并发执行，失败的步骤可重试。') },
      { title: bi('Human review at the boundary', '保留人工确认'), text: bi('Users supply missing experience and approve CV edits before export. Interview practice remains an explicit choice, not an automatic action.', '缺失经历由用户补充，简历修改经用户确认后导出。模拟面试始终需要用户主动选择。') },
    ],
    decisions: [
      { title: bi('From process to outcomes', '从过程转向成果'), before: bi('Useful results were squeezed beside lengthy execution messages.', '有用的结果挤在一旁，大部分空间展示执行过程。'), after: bi('I requested a results-first workspace with a clear waiting state and no verbose reasoning stream.', '我要求改为成果优先的工作区，并使用明确的等待提示，不展示冗长推理。') },
      { title: bi('Less advice, more substance', '建议可以少，但要有实质变化'), before: bi('Some “improvements” only changed punctuation or repeated the source.', '部分“修改建议”只换标点，或几乎重复原文。'), after: bi('I required ineffective rewrites to be filtered and genuine extra experience to be collected when useful evidence was missing.', '我要求过滤无效改写；缺少有用证据时，让用户补充真实经历。') },
    ],
    limits: bi('This is a bounded, model-assisted workflow, not an unrestricted autonomous agent. It does not browse recruitment sites, submit applications or continue running after the browser is closed. Text-based fact checks reduce risk but do not guarantee factual correctness.', '这是有边界的模型辅助工作流，并非无限自主 Agent。它不浏览招聘网站、不提交申请，也不会在关闭浏览器后继续执行。文本事实校验用于降低风险，不能保证内容绝对正确。'),
    evidence: [
      { label: bi('Tool selection', '工具选择'), path: 'backend/app/ai/agent.py' },
      { label: bi('State & execution', '状态与执行'), path: 'backend/app/api/routes/agent.py' },
      { label: bi('Workflow tests', '工作流测试'), path: 'backend/tests/test_agent.py' },
    ],
  },
  {
    id: 'ai-persona', number: '02', name: bi('AI Persona', 'AI 分身'), accent: 'sand', route: '/me', image: bi('/portfolio/persona.png', '/portfolio/persona-zh.png'),
    purpose: bi('Get to know the creator', '通过对话，了解我'),
    enter: bi('Start a conversation', '开始对话'),
    tag: bi('Grounded conversation · Public facts', '有依据的对话 · 公开资料'),
    summary: bi('A conversational interface to my projects and decisions, grounded in a curated set of public information.', '以经过整理的公开资料为依据，通过对话了解我的项目、经历与决策。'),
    question: bi('How can a personal AI feel conversational without inventing the person behind it?', '如何让个人 AI 自然交流，同时不编造本人经历？'),
    problem: bi('A static CV is brief, while an open-ended chatbot can make unsupported claims. I wanted visitors to ask follow-up questions about real projects in a familiar chat interface.', '静态简历篇幅有限，开放式聊天又可能夸大经历。我希望访客能在熟悉的聊天界面里追问真实项目。'),
    owned: bi('I conceived the AI persona, asked for model-generated conversation rather than canned retrieval, selected the chat-app interaction style and approved which personal information could be public.', '我提出 AI 分身的想法，要求接入模型自然对话而非机械检索，确定聊天软件式交互，并确认哪些个人信息可以公开。'),
    steps: [bi('Visitor asks a question', '访客提出问题'), bi('Curated public context', '载入整理后的公开资料'), bi('Generate a bounded reply', '生成有边界的回答'), bi('Check referenced fact IDs', '校验引用的资料标识')],
    mechanisms: [
      { title: bi('Explicit knowledge boundary', '明确的知识边界'), text: bi('The model receives curated public facts and recent dialogue. Visitor messages are context, not a source of new biographical claims.', '模型使用整理后的公开事实和近期对话。访客消息用于理解上下文，不能变成本人的新经历。') },
      { title: bi('Structured replies', '结构化回复'), text: bi('Replies contain answer text and fact identifiers. Unknown identifiers trigger a fallback; the interface clearly identifies the speaker as an AI persona.', '回复包含正文与资料标识。未知标识会触发兜底，界面明确告知这是 AI 分身。') },
      { title: bi('Separated private data', '隔离访客私有资料'), text: bi('The persona does not read a visitor’s uploaded CV or private profile. Contact details are supplied to the model only for a contact-related question.', '分身不读取访客上传的简历或私有档案。只有联系类问题才会向模型提供本人联系方式。') },
    ],
    decisions: [
      { title: bi('Conversation, not information cards', '自然对话，而非资料卡拼接'), before: bi('Mechanical answers did not feel like a useful personal conversation.', '机械回答无法形成有用的个人交流。'), after: bi('I requested natural model-generated answers and follow-up support, with clear limits on unconfirmed information.', '我要求模型自然生成回答并支持追问，同时限制未确认的信息。') },
      { title: bi('Accessible without pretending', '便于交流，但不冒充真人'), before: bi('A realistic chat interface could be mistaken for a live reply from me.', '真实感较强的聊天界面可能被误认为本人在线回复。'), after: bi('The interface identifies the AI persona, while keeping the conversation itself concise and natural.', '界面明确标注 AI 分身，同时保持对话简洁自然。') },
    ],
    limits: bi('This uses curated context, not a fine-tuned model or a vector-retrieval system. Fact IDs are a traceability check, not proof that every sentence is supported. The persona cannot commit to offers, admissions decisions or availability on my behalf.', '它使用整理后的上下文，并非微调模型或向量检索系统。资料标识用于溯源，不能证明每句话都有充分依据。分身不能代替本人作出录用、申请或时间安排承诺。'),
    evidence: [
      { label: bi('Reply pipeline', '回复流程'), path: 'backend/app/api/routes/persona.py' },
      { label: bi('Public facts', '公开资料'), path: 'backend/app/persona_public.json' },
      { label: bi('Privacy & response tests', '隐私与回复测试'), path: 'backend/tests/test_persona.py' },
    ],
  },
  {
    id: 'zhitu-cv', number: '03', name: bi('Zhitu CV', '职途简历'), accent: 'blue', route: '/app', image: bi('/portfolio/toolkit.png', '/portfolio/toolkit-zh.png'),
    purpose: bi('Use individual CV tools', '按需使用，逐步完善简历'),
    enter: bi('Open the workspace', '进入简历工作台'),
    tag: bi('Full-stack application · Document workflow', '全栈应用 · 文档工作流'),
    summary: bi('The foundation of the studio: CV parsing, role matching, editable recommendations and finished PDF / Word documents.', '整个工作室的基础：简历解析、岗位匹配、可编辑建议，以及可直接使用的 PDF / Word 文档。'),
    question: bi('How can AI advice become a usable document while preserving the applicant’s real experience?', '如何保留申请者的真实经历，并将 AI 建议转化为可用文档？'),
    problem: bi('Advice alone still leaves users to rewrite and lay out a CV. I wanted a complete path from upload and confirmation to an editable, properly formatted document.', '只有建议仍需要用户自己改写和排版。我希望打通上传、确认、编辑到成品文档的完整流程。'),
    owned: bi('I defined the core features, supplied a layout reference, requested original-versus-suggestion review and added Word export so users could keep editing their own documents.', '我确定核心功能、提供排版参考，提出原文与建议对照确认，并要求加入 Word 导出，方便用户继续编辑。'),
    steps: [bi('Upload and confirm text', '上传并确认文本'), bi('Analyse or tailor', '分析或定制'), bi('Review individual changes', '逐条确认修改'), bi('Export PDF or Word', '导出 PDF 或 Word')],
    mechanisms: [
      { title: bi('Document-to-data pipeline', '文档到数据的流程'), text: bi('PDF and DOCX text is extracted and checked by the user before AI features consume it. Files are accessed through private, user-scoped endpoints.', 'PDF 与 DOCX 文本提取后先由用户确认，再供 AI 功能使用。文件通过按用户隔离的私有接口访问。') },
      { title: bi('Reviewable edits', '可检查的修改'), text: bi('Recommendations retain source text, suggested wording and a user decision. Cosmetic changes are filtered rather than counted as meaningful improvements.', '建议保留原文、改写与用户决策。仅有表面变化的内容会被过滤，不计为实质改进。') },
      { title: bi('Two useful output formats', '两种实用输出格式'), text: bi('A shared CV structure feeds PDF and editable Word exports. Layout and content validation are separate concerns from the model’s writing.', '统一简历结构用于 PDF 与可编辑 Word 导出。排版、内容校验与模型写作分别处理。') },
    ],
    decisions: [
      { title: bi('A finished CV, not a text dump', '需要成品简历，而非纯文字输出'), before: bi('The first export looked like a plain text document.', '早期导出看起来只是纯文字文档。'), after: bi('I supplied a template reference and asked for a consistent CV layout with editable Word export.', '我提供模板参考，要求统一简历排版，并加入可编辑 Word 导出。') },
      { title: bi('Keep genuine experience reusable', '让真实经历可复用'), before: bi('One short CV could not contain all relevant experience for different roles.', '一份短简历无法包含适合不同岗位的所有经历。'), after: bi('I requested a separate store for additional skills and experiences, so role-specific selection has more genuine material.', '我提出单独保存补充技能与经历，为岗位定制提供更多真实材料。') },
    ],
    limits: bi('Scanned-image OCR is not supported. A match score is a model-assisted heuristic, not a hiring probability. Source checks and human review reduce fabrication risk but do not eliminate it.', '暂不支持扫描图片 OCR。匹配分是模型辅助的启发式评估，不是录用概率。原文校验与人工确认可以降低虚构风险，但不能完全消除。'),
    evidence: [
      { label: bi('Meaningful-edit tests', '实质修改测试'), path: 'backend/tests/test_meaningful_suggestions.py' },
      { label: bi('CV export tests', '简历导出测试'), path: 'backend/tests/test_custom_resume.py' },
      { label: bi('Access & security tests', '访问与安全测试'), path: 'backend/tests/test_security.py' },
    ],
  },
]
