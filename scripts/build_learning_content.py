#!/usr/bin/env python3
"""Build the reviewed paper- and presentation-based learning content."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

import pyphen


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
APP_DATA = ROOT / "app" / "data"
PRESENTATION_VOCAB = DATA / "presentation_vocabulary.psv"

WORD_DATA = """
protein|蛋白质|noun|proteomics
cell|细胞|noun|cell-biology
activity|活性|noun|methods
expression|表达|noun|molecular-biology
function|功能|noun|molecular-biology
ubiquitin|泛素|noun|ubiquitin
response|反应|noun|immunology
binding|结合|noun|molecular-biology
target|靶点|noun|drug-discovery
gene|基因|noun|molecular-biology
activation|激活|noun|cell-biology
proteomics|蛋白质组学|noun|proteomics
inhibition|抑制|noun|drug-discovery
regulation|调控|noun|molecular-biology
enzyme|酶|noun|protease
pathway|通路|noun|cell-biology
mechanism|机制|noun|communication
domain|结构域|noun|molecular-biology
proteome|蛋白质组|noun|proteomics
sample|样本|noun|methods
inhibitor|抑制剂|noun|drug-discovery
growth|生长|noun|cell-biology
peptide|肽|noun|mass-spec
tissue|组织|noun|cell-biology
immune|免疫的|adjective|immunology
residue|残基|noun|molecular-biology
treatment|治疗|noun|clinical
substrate|底物|noun|protease
modification|修饰|noun|molecular-biology
identification|鉴定|noun|mass-spec
metabolism|代谢|noun|metabolism
antigen|抗原|noun|immunology
signaling|信号传导|noun|cell-biology
proteasome|蛋白酶体|noun|ubiquitin
profiling|谱分析|noun|proteomics
site|位点|noun|molecular-biology
transcription|转录|noun|molecular-biology
infection|感染|noun|immunology
protease|蛋白酶|noun|protease
receptor|受体|noun|cell-biology
specificity|特异性|noun|methods
processing|加工处理|noun|cell-biology
interaction|相互作用|noun|molecular-biology
degradation|降解|noun|ubiquitin
stress|应激|noun|cell-biology
repair|修复|noun|molecular-biology
recognition|识别|noun|immunology
accumulation|积累|noun|cell-biology
damage|损伤|noun|molecular-biology
formation|形成|noun|cell-biology
inflammation|炎症|noun|immunology
discovery|发现|noun|drug-discovery
molecule|分子|noun|molecular-biology
regulator|调节因子|noun|molecular-biology
detection|检测|noun|methods
chromatography|色谱|noun|mass-spec
mutation|突变|noun|molecular-biology
replication|复制|noun|molecular-biology
phosphorylation|磷酸化|noun|molecular-biology
sensitivity|灵敏度|noun|methods
biomarker|生物标志物|noun|clinical
cycle|周期|noun|cell-biology
plasma|血浆|noun|clinical
ligase|连接酶|noun|ubiquitin
sequence|序列|noun|molecular-biology
survival|存活|noun|clinical
RNA|核糖核酸|abbreviation|molecular-biology
membrane|膜|noun|cell-biology
component|组分|noun|molecular-biology
alteration|改变|noun|molecular-biology
mitochondrial|线粒体的|adjective|cell-biology
intracellular|细胞内的|adjective|cell-biology
selectivity|选择性|noun|drug-discovery
abundance|丰度|noun|proteomics
structure|结构|noun|molecular-biology
lysine|赖氨酸|noun|ubiquitin
probe|探针|noun|methods
chain|链|noun|ubiquitin
cysteine|半胱氨酸|noun|protease
progression|进展|noun|clinical
apoptosis|细胞凋亡|noun|cell-biology
histone|组蛋白|noun|molecular-biology
kinase|激酶|noun|molecular-biology
covalent|共价的|adjective|molecular-biology
labeling|标记|noun|methods
chromatin|染色质|noun|molecular-biology
stability|稳定性|noun|molecular-biology
ubiquitylation|泛素化|noun|ubiquitin
ubiquitination|泛素化|noun|ubiquitin
genome|基因组|noun|molecular-biology
assay|实验测定|noun|methods
enrichment|富集|noun|proteomics
recruitment|募集|noun|cell-biology
cleavage|切割|noun|protease
acute|急性的|adjective|clinical
mammalian|哺乳动物的|adjective|cell-biology
homeostasis|稳态|noun|cell-biology
proliferation|增殖|noun|cell-biology
proteolysis|蛋白水解|noun|protease
depletion|耗竭或敲低|noun|methods
phenotype|表型|noun|cell-biology
candidate|候选物|noun|drug-discovery
posttranslational|翻译后的|adjective|molecular-biology
synthesis|合成|noun|molecular-biology
composition|组成|noun|proteomics
methylation|甲基化|noun|molecular-biology
characterization|表征|noun|methods
workflow|工作流程|noun|methods
epitope|表位|noun|immunology
cytotoxic|细胞毒性的|adjective|immunology
performance|性能|noun|methods
signature|特征标志|noun|proteomics
differential|差异的|adjective|methods
therapy|治疗方法|noun|clinical
differentiation|分化|noun|cell-biology
proteasomal|蛋白酶体的|adjective|ubiquitin
turnover|周转|noun|ubiquitin
downstream|下游的|adjective|cell-biology
hypoxia|低氧|noun|cell-biology
deficiency|缺陷|noun|clinical
subunit|亚基|noun|molecular-biology
enzymatic|酶促的|adjective|protease
validation|验证|noun|methods
innate|先天的|adjective|immunology
lymphocyte|淋巴细胞|noun|immunology
reticulum|网状结构|noun|cell-biology
genomic|基因组的|adjective|molecular-biology
antibody|抗体|noun|immunology
ligand|配体|noun|molecular-biology
upregulation|上调|noun|molecular-biology
translation|翻译|noun|molecular-biology
transport|运输|noun|cell-biology
acetylation|乙酰化|noun|molecular-biology
collagen|胶原蛋白|noun|cell-biology
affinity|亲和力|noun|molecular-biology
sequencing|测序|noun|methods
lipid|脂质|noun|metabolism
variant|变异|noun|molecular-biology
bacterial|细菌的|adjective|immunology
epigenetic|表观遗传的|adjective|molecular-biology
network|网络|noun|cell-biology
oxidative|氧化的|adjective|cell-biology
autophagy|自噬|noun|cell-biology
viability|活力|noun|cell-biology
aggregation|聚集|noun|proteomics
effector|效应分子|noun|immunology
localization|定位|noun|cell-biology
quantification|定量|noun|mass-spec
deubiquitinase|去泛素化酶|noun|ubiquitin
interactor|相互作用蛋白|noun|molecular-biology
cytotoxicity|细胞毒性|noun|immunology
secretion|分泌|noun|cell-biology
resistance|抗性|noun|clinical
invasion|侵袭|noun|clinical
reversible|可逆的|adjective|molecular-biology
capacity|能力|noun|methods
concentration|浓度|noun|methods
machinery|分子机器|noun|cell-biology
potency|效力|noun|drug-discovery
metabolite|代谢物|noun|metabolism
microscopy|显微镜技术|noun|methods
modulation|调节|noun|molecular-biology
physiological|生理的|adjective|cell-biology
conformational|构象的|adjective|molecular-biology
deacetylase|去乙酰化酶|noun|molecular-biology
engagement|结合占有|noun|drug-discovery
fibroblast|成纤维细胞|noun|cell-biology
fragment|片段|noun|mass-spec
hydroxylase|羟化酶|noun|molecular-biology
mortality|死亡率|noun|clinical
mRNA|信使RNA|abbreviation|molecular-biology
neuronal|神经元的|adjective|cell-biology
pathogen|病原体|noun|immunology
preparation|制备|noun|methods
resolution|分辨率|noun|mass-spec
suppression|抑制|noun|molecular-biology
transporter|转运体|noun|cell-biology
checkpoint|检查点|noun|cell-biology
endosomal|内体的|adjective|cell-biology
complexity|复杂性|noun|communication
DNA|脱氧核糖核酸|abbreviation|molecular-biology
mechanistic|机制性的|adjective|communication
matrix|基质|noun|cell-biology
extracellular|细胞外的|adjective|cell-biology
nuclear|细胞核的|adjective|cell-biology
transcriptional|转录的|adjective|molecular-biology
endogenous|内源性的|adjective|molecular-biology
structural|结构的|adjective|molecular-biology
pathological|病理性的|adjective|clinical
therapeutic|治疗性的|adjective|clinical
quantitative|定量的|adjective|methods
functional|功能性的|adjective|methods
selective|选择性的|adjective|drug-discovery
regulatory|调节性的|adjective|molecular-biology
objective|研究目标|noun|communication
evidence|证据|noun|communication
implication|意义或影响|noun|communication
conclusion|结论|noun|communication
hypothesis|假设|noun|communication
reproducibility|可重复性|noun|communication
""".strip()

PHRASE_DATA = """
mass spectrometry|质谱|mass-spec
tandem mass spectrometry|串联质谱|mass-spec
liquid chromatography|液相色谱|mass-spec
LC-MS/MS|液相色谱-串联质谱|mass-spec
quantitative proteomics|定量蛋白质组学|proteomics
functional proteomics|功能蛋白质组学|proteomics
quantitative mass spectrometry|定量质谱|mass-spec
sample preparation|样品制备|methods
protein profiling|蛋白质谱分析|proteomics
protein abundance|蛋白质丰度|proteomics
proteomic signature|蛋白质组特征|proteomics
ubiquitin ligase|泛素连接酶|ubiquitin
ubiquitin chain|泛素链|ubiquitin
ubiquitin-proteasome system|泛素-蛋白酶体系统|ubiquitin
deubiquitinating enzyme|去泛素化酶|ubiquitin
deubiquitylating enzyme|去泛素化酶|ubiquitin
proteasome activity|蛋白酶体活性|ubiquitin
proteasome inhibitor|蛋白酶体抑制剂|ubiquitin
cysteine protease|半胱氨酸蛋白酶|protease
active site|活性位点|protease
catalytic domain|催化结构域|protease
catalytic activity|催化活性|protease
target engagement|靶点结合|drug-discovery
therapeutic target|治疗靶点|drug-discovery
small molecule|小分子|drug-discovery
post-translational modification|翻译后修饰|molecular-biology
lysine residue|赖氨酸残基|ubiquitin
cysteine residue|半胱氨酸残基|protease
amino acid|氨基酸|molecular-biology
side chain|侧链|molecular-biology
protein degradation|蛋白质降解|ubiquitin
protein turnover|蛋白质周转|ubiquitin
gene expression|基因表达|molecular-biology
transcription factor|转录因子|molecular-biology
transcriptional activation|转录激活|molecular-biology
DNA damage|DNA损伤|molecular-biology
DNA repair|DNA修复|molecular-biology
DNA replication|DNA复制|molecular-biology
replication stress|复制应激|molecular-biology
genome stability|基因组稳定性|molecular-biology
cell cycle|细胞周期|cell-biology
cell proliferation|细胞增殖|cell-biology
cell survival|细胞存活|cell-biology
cell death|细胞死亡|cell-biology
oxidative stress|氧化应激|cell-biology
reactive oxygen species|活性氧|cell-biology
immune response|免疫反应|immunology
innate immune response|先天免疫反应|immunology
antigen processing|抗原加工|immunology
antigen presentation|抗原呈递|immunology
major histocompatibility complex|主要组织相容性复合体|immunology
endoplasmic reticulum|内质网|cell-biology
extracellular matrix|细胞外基质|cell-biology
biomarker discovery|生物标志物发现|clinical
molecular signature|分子特征|proteomics
protein aggregation|蛋白质聚集|proteomics
protein-protein interaction|蛋白质相互作用|molecular-biology
loss of function|功能缺失|molecular-biology
gain of function|功能获得|molecular-biology
mechanism of action|作用机制|drug-discovery
""".strip()

SENTENCE_DATA = """
Thank you for taking the time to meet with me today.|感谢您今天抽时间与我会面。
My name is Tao Ding, and I am a PhD candidate at Peking Union Medical College.|我叫丁涛，是北京协和医学院的博士研究生。
My current project focuses on protein lactylation in C. elegans.|我目前的课题聚焦于秀丽隐杆线虫中的蛋白质乳酸化。
I use mass spectrometry-based proteomics to characterize post-translational modifications.|我使用基于质谱的蛋白质组学来表征翻译后修饰。
The main question is how these modifications affect protein function and cellular pathways.|核心问题是这些修饰如何影响蛋白质功能和细胞通路。
I would like to briefly introduce my current work.|我想简要介绍一下目前的工作。
This slide shows the overall experimental workflow.|这张幻灯片展示了总体实验流程。
First, we collected samples under the indicated conditions.|首先，我们在指定条件下收集了样本。
We then performed protein extraction, digestion, and LC-MS/MS analysis.|随后，我们进行了蛋白提取、酶解和LC-MS/MS分析。
The data were analyzed to identify differentially modified proteins.|我们分析数据以鉴定差异修饰蛋白。
Our preliminary results suggest that several metabolic pathways may be involved.|我们的初步结果提示可能涉及若干代谢通路。
We observed enrichment in several metabolic pathways.|我们观察到若干代谢通路出现富集。
One possible explanation is that the modification alters protein stability.|一种可能的解释是该修饰改变了蛋白质稳定性。
However, this interpretation still requires further validation.|不过，这一解释仍需进一步验证。
The main limitation is the current sample size.|主要局限是目前的样本量。
We are currently repeating the key experiments.|我们目前正在重复关键实验。
I am particularly interested in your work on ubiquitin and protease biology.|我尤其对您在泛素和蛋白酶生物学方面的研究感兴趣。
I would like to learn activity-based proteomics in your laboratory.|我希望在您的实验室学习活性导向的蛋白质组学。
I am also interested in combining ubiquitin profiling with quantitative mass spectrometry.|我也对将泛素谱分析与定量质谱相结合感兴趣。
During the visit, I hope to develop a focused and feasible project.|访学期间，我希望开展一个聚焦且可行的项目。
I would be happy to adapt the plan to your group's current priorities.|我愿意根据您课题组当前的重点调整计划。
Could you please advise me on which direction would be most useful?|您能否建议哪个方向最有价值？
Which part of this project do you think is most feasible?|您认为这个项目的哪一部分最可行？
Are there any ongoing projects that I could contribute to?|是否有我可以参与的在研项目？
I would appreciate the opportunity to learn from your team.|如果有机会向您的团队学习，我将非常感谢。
Sorry, could you please say that again more slowly?|抱歉，您能否再慢一点说一遍？
Could you please rephrase the question?|您能换一种方式表述这个问题吗？
If I understood correctly, you are asking about the experimental design.|如果我理解正确，您是在询问实验设计。
I caught the first part, but I missed the last point.|我听懂了前半部分，但没有听清最后一点。
Could you please type the key term in the chat?|您能把关键词打在聊天框里吗？
May I take a moment to think?|可以让我稍微想一下吗？
I do not have the exact answer yet, but my current understanding is as follows.|我目前还没有确切答案，但我的理解如下。
That is an important point, and I will look into it carefully.|这是一个重要问题，我会认真研究。
I will follow up with the relevant data after the meeting.|会后我会补充相关数据。
Would it be all right if I followed up by email?|我稍后通过邮件补充可以吗？
The proposed visit would need to be completed within the approved period.|拟议访学需要在获批期限内完成。
I will provide the required documents as soon as possible.|我会尽快提供所需材料。
Thank you for your helpful suggestions.|感谢您的宝贵建议。
I have learned a great deal from this discussion.|我从这次讨论中学到了很多。
I look forward to the possibility of working with you and your team.|我期待有机会与您和您的团队合作。
""".strip()


CUSTOM_IPA = {
    "inhibitor": "/ɪnˈhɪbɪtə/",
    "immune": "/ɪˈmjuːn/",
    "residue": "/ˈrezɪdjuː/",
    "antigen": "/ˈæntɪdʒən/",
    "signaling": "/ˈsɪɡnəlɪŋ/",
    "profiling": "/ˈprəʊfaɪlɪŋ/",
    "RNA": "/ˌɑːr en ˈeɪ/",
    "intracellular": "/ˌɪntrəˈseljʊlə/",
    "selectivity": "/sɪˌlekˈtɪvəti/",
    "labeling": "/ˈleɪbəlɪŋ/",
    "cleavage": "/ˈkliːvɪdʒ/",
    "mammalian": "/mæˈmeɪliən/",
    "posttranslational": "/ˌpəʊsttrænzˈleɪʃənəl/",
    "epitope": "/ˈepɪtəʊp/",
    "cytotoxic": "/ˌsaɪtəʊˈtɒksɪk/",
    "performance": "/pəˈfɔːməns/",
    "differential": "/ˌdɪfəˈrenʃəl/",
    "proteasomal": "/ˈprəʊtiəsəʊməl/",
    "turnover": "/ˈtɜːnəʊvə/",
    "hypoxia": "/haɪˈpɒksiə/",
    "lymphocyte": "/ˈlɪmfəsaɪt/",
    "reticulum": "/rɪˈtɪkjʊləm/",
    "genomic": "/dʒɪˈnəʊmɪk/",
    "upregulation": "/ˌʌpreɡjʊˈleɪʃən/",
    "acetylation": "/əˌsiːtɪˈleɪʃən/",
    "sequencing": "/ˈsiːkwənsɪŋ/",
    "bacterial": "/bækˈtɪəriəl/",
    "oxidative": "/ˈɒksɪdətɪv/",
    "autophagy": "/ɔːˈtɒfədʒi/",
    "viability": "/ˌvaɪəˈbɪləti/",
    "cytotoxicity": "/ˌsaɪtəʊtɒkˈsɪsəti/",
    "secretion": "/sɪˈkriːʃən/",
    "deacetylase": "/ˌdiːəˈsetɪleɪz/",
    "mortality": "/mɔːˈtæləti/",
    "mRNA": "/ˌem ɑːr en ˈeɪ/",
    "neuronal": "/njʊəˈrəʊnəl/",
    "checkpoint": "/ˈtʃekpɔɪnt/",
    "endosomal": "/ˈendəʊsəʊməl/",
    "DNA": "/ˌdiː en ˈeɪ/",
    "extracellular": "/ˌekstrəˈseljʊlə/",
    "transcriptional": "/trænˈskrɪpʃənəl/",
    "structural": "/ˈstrʌktʃərəl/",
    "reproducibility": "/ˌriːprədjuːsəˈbɪləti/",
    "ubiquitin": "/juːˈbɪkwɪtɪn/",
    "proteomics": "/ˌprəʊtiˈɒmɪks/",
    "proteome": "/ˈprəʊtiəʊm/",
    "proteasome": "/ˈprəʊtiəsəʊm/",
    "spectrometry": "/spɛkˈtrɒmɪtri/",
    "chromatography": "/ˌkrəʊməˈtɒɡrəfi/",
    "ubiquitylation": "/juːˌbɪkwɪtɪˈleɪʃən/",
    "ubiquitination": "/juːˌbɪkwɪtɪˈneɪʃən/",
    "deubiquitinase": "/ˌdiːjuːˈbɪkwɪtɪneɪz/",
    "phosphorylation": "/ˌfɒsfərɪˈleɪʃən/",
    "apoptosis": "/ˌeɪpɒpˈtəʊsɪs/",
    "proteolysis": "/ˌprəʊtiˈɒlɪsɪs/",
    "lysine": "/ˈlaɪsiːn/",
    "cysteine": "/ˈsɪstiːn/",
    "histone": "/ˈhɪstəʊn/",
    "hydroxylase": "/haɪˈdrɒksɪleɪz/",
    "proteomic": "/ˌprəʊtiˈɒmɪk/",
    "deubiquitinating": "/ˌdiːjuːˈbɪkwɪtɪneɪtɪŋ/",
    "deubiquitylating": "/ˌdiːjuːˈbɪkwɪtɪleɪtɪŋ/",
    "histocompatibility": "/ˌhɪstəʊkəmˌpætəˈbɪləti/",
    "mass spectrometry": "/mæs spɛkˈtrɒmɪtri/",
    "tandem mass spectrometry": "/ˈtændəm mæs spɛkˈtrɒmɪtri/",
    "liquid chromatography": "/ˈlɪkwɪd ˌkrəʊməˈtɒɡrəfi/",
    "LC-MS/MS": "/ˌɛl siː ˌɛm ɛs ˌɛm ɛs/",
    "antigen presentation": "/ˈæntɪdʒən ˌprezənˈteɪʃən/",
    "endoplasmic reticulum": "/ˌendəʊˈplæzmɪk rɪˈtɪkjʊləm/",
}

PRONOUNCE_AS = {
    "RNA": "R N A",
    "mRNA": "M R N A",
    "DNA": "D N A",
    "LC-MS/MS": "L C M S M S",
    "C. elegans": "C elegans",
}

FAMILIES = {
    "expression": ["express", "expressed", "expression"],
    "activation": ["activate", "active", "activation"],
    "inhibition": ["inhibit", "inhibitor", "inhibitory", "inhibition"],
    "regulation": ["regulate", "regulator", "regulatory", "regulation"],
    "identification": ["identify", "identified", "identification"],
    "modification": ["modify", "modified", "modification"],
    "degradation": ["degrade", "degraded", "degradation"],
    "detection": ["detect", "detectable", "detection"],
    "replication": ["replicate", "replication"],
    "sensitivity": ["sensitive", "sensitivity"],
    "survival": ["survive", "survival"],
    "alteration": ["alter", "altered", "alteration"],
    "abundance": ["abundant", "abundance"],
    "progression": ["progress", "progression"],
    "stability": ["stable", "stability"],
    "enrichment": ["enrich", "enriched", "enrichment"],
    "recruitment": ["recruit", "recruitment"],
    "proliferation": ["proliferate", "proliferation"],
    "depletion": ["deplete", "depleted", "depletion"],
    "characterization": ["characterize", "characterized", "characterization"],
    "validation": ["validate", "validated", "validation"],
    "differentiation": ["differentiate", "differentiation"],
    "localization": ["localize", "localized", "localization"],
    "quantification": ["quantify", "quantitative", "quantification"],
    "modulation": ["modulate", "modulation"],
    "suppression": ["suppress", "suppressor", "suppression"],
    "therapeutic": ["therapy", "therapeutic"],
    "functional": ["function", "functional"],
    "selective": ["select", "selection", "selective", "selectivity"],
    "hypothesis": ["hypothesis", "hypothesize"],
    "conclusion": ["conclude", "conclusion"],
}

CONTEXT_EN = {
    "ubiquitin": "ubiquitin and protease biology",
    "protease": "protease activity and substrate cleavage",
    "mass-spec": "mass-spectrometry experiments",
    "proteomics": "quantitative proteomics",
    "molecular-biology": "molecular regulation",
    "cell-biology": "cellular pathways",
    "immunology": "immune responses",
    "clinical": "disease mechanisms",
    "drug-discovery": "target discovery",
    "metabolism": "cellular metabolism",
    "methods": "the experimental workflow",
    "communication": "the interpretation of the results",
}

CONTEXT_ZH = {
    "ubiquitin": "泛素和蛋白酶生物学",
    "protease": "蛋白酶活性与底物切割",
    "mass-spec": "质谱实验",
    "proteomics": "定量蛋白质组学",
    "molecular-biology": "分子调控",
    "cell-biology": "细胞通路",
    "immunology": "免疫反应",
    "clinical": "疾病机制",
    "drug-discovery": "靶点发现",
    "metabolism": "细胞代谢",
    "methods": "实验流程",
    "communication": "结果解读",
}


def parse_rows(value: str, fields: int) -> list[list[str]]:
    rows = []
    for line in value.splitlines():
        values = [item.strip() for item in line.split("|")]
        if len(values) != fields:
            raise ValueError(f"Expected {fields} fields: {line}")
        rows.append(values)
    return rows


def normalize(value: str) -> str:
    value = value.lower().replace("–", "-").replace("—", "-")
    value = value.replace("post-translational", "posttranslational")
    value = value.replace("protein-protein", "protein protein")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def write_text_lf(path: Path, value: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value)


def phonetic(term: str) -> str:
    if term in CUSTOM_IPA:
        return CUSTOM_IPA[term]
    ipa_path = DATA / "uk_ipa.json"
    if ipa_path.exists():
        return json.loads(ipa_path.read_text(encoding="utf-8")).get(term, "")
    return ""


def main() -> None:
    APP_DATA.mkdir(parents=True, exist_ok=True)
    bundle = json.loads((DATA / "publications.json").read_text(encoding="utf-8"))
    publications = bundle["publications"]
    publication_by_id = {item["corpusId"]: item for item in publications}

    word_candidates = {}
    with (DATA / "word_candidates.csv").open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            word_candidates[row["term"].lower()] = row

    hyphenator = pyphen.Pyphen(lang="en_GB")

    def find_sources(term: str, aliases: list[str] | None = None) -> list[str]:
        search_terms = [term] + (aliases or [])
        normalized_terms = [normalize(item) for item in search_terms]
        matches = []
        for pub in publications:
            haystack = normalize(pub["title"] + " " + pub["abstract"])
            if any(re.search(rf"\b{re.escape(needle)}\b", haystack) for needle in normalized_terms):
                matches.append(pub["corpusId"])
                if len(matches) >= 3:
                    break
        return matches

    def source_payload(source_ids: list[str]) -> dict:
        if not source_ids:
            return {"sourceIds": [], "sourceTitle": "", "sourceDoi": ""}
        first = publication_by_id[source_ids[0]]
        return {
            "sourceIds": source_ids,
            "sourceTitle": first["title"],
            "sourceDoi": first["doi"],
        }

    word_rows = parse_rows(WORD_DATA, 4)
    phrase_rows = parse_rows(PHRASE_DATA, 3)
    sentence_rows = parse_rows(SENTENCE_DATA, 2)
    if (len(word_rows), len(phrase_rows), len(sentence_rows)) != (200, 60, 40):
        raise ValueError(
            f"Expected 200 words, 60 phrases, 40 sentences; got "
            f"{len(word_rows)}, {len(phrase_rows)}, {len(sentence_rows)}"
        )

    items = []
    missing_sources = []
    word_aliases = {
        "fibroblast": ["fibroblasts"],
        "implication": ["implications"],
    }

    for index, (term, zh, part_of_speech, theme) in enumerate(word_rows, start=1):
        lookup = word_candidates.get(term.lower())
        source_ids = []
        corpus_frequency = 0
        document_frequency = 0
        if lookup:
            source_ids = [item for item in lookup["sourceIds"].split(";") if item][:3]
            corpus_frequency = int(lookup["termFrequency"])
            document_frequency = int(lookup["documentFrequency"])
        else:
            source_ids = find_sources(term, word_aliases.get(term.lower()))
        if not source_ids:
            missing_sources.append(term)

        if part_of_speech == "adjective":
            example_en = f"This {term.lower()} change may affect {CONTEXT_EN[theme]}."
            example_zh = f"这种{zh}变化可能影响{CONTEXT_ZH[theme]}。"
        elif part_of_speech == "abbreviation":
            example_en = f"We measured {term} in the selected samples."
            example_zh = f"我们在所选样本中检测了{zh}。"
        else:
            example_en = f"We discussed the role of {term.lower()} in {CONTEXT_EN[theme]}."
            example_zh = f"我们讨论了{zh}在{CONTEXT_ZH[theme]}中的作用。"

        item = {
            "id": f"ME-W{index:03d}",
            "type": "word",
            "tier": "meeting",
            "rank": index,
            "dailyPriority": 1,
            "term": term,
            "displayTerm": term,
            "chinese": zh,
            "partOfSpeech": part_of_speech,
            "theme": theme,
            "ipa": phonetic(term),
            "syllables": hyphenator.inserted(term.lower(), hyphen="·"),
            "wordFamily": FAMILIES.get(term.lower(), [term]),
            "exampleEnglish": example_en,
            "exampleChinese": example_zh,
            "pronounceAs": PRONOUNCE_AS.get(term, term),
            "documentFrequency": document_frequency,
            "corpusFrequency": corpus_frequency,
            "reviewStatus": "manually-reviewed-meeting-tier",
            **source_payload(source_ids),
        }
        items.append(item)

    phrase_aliases = {
        "LC-MS/MS": ["liquid chromatography tandem mass spectrometry", "lc ms ms"],
        "post-translational modification": ["posttranslational modification"],
        "protein-protein interaction": ["protein protein interaction"],
    }
    for index, (term, zh, theme) in enumerate(phrase_rows, start=1):
        source_ids = find_sources(term, phrase_aliases.get(term))
        if not source_ids:
            missing_sources.append(term)
        example_en = f"The project examines {term} in a relevant biological context."
        example_zh = f"该项目在相关生物学背景下研究{zh}。"
        items.append(
            {
                "id": f"ME-P{index:03d}",
                "type": "phrase",
                "tier": "meeting",
                "rank": index,
                "dailyPriority": 1,
                "term": term,
                "displayTerm": term,
                "chinese": zh,
                "partOfSpeech": "noun phrase",
                "theme": theme,
                "ipa": phonetic(term),
                "syllables": " ".join(
                    hyphenator.inserted(word, hyphen="·") for word in term.lower().split()
                ),
                "wordFamily": [term],
                "exampleEnglish": example_en,
                "exampleChinese": example_zh,
                "pronounceAs": PRONOUNCE_AS.get(term, term),
                "documentFrequency": len(source_ids),
                "corpusFrequency": 0,
                "reviewStatus": "manually-reviewed-meeting-tier",
                **source_payload(source_ids),
            }
        )

    for index, (sentence, zh) in enumerate(sentence_rows, start=1):
        pronounce_as = sentence.replace("LC-MS/MS", "L C M S M S").replace(
            "C. elegans", "C elegans"
        )
        items.append(
            {
                "id": f"ME-S{index:03d}",
                "type": "sentence",
                "tier": "meeting",
                "rank": index,
                "dailyPriority": 1,
                "term": sentence,
                "displayTerm": sentence,
                "chinese": zh,
                "partOfSpeech": "scientific communication",
                "theme": "communication",
                "ipa": "",
                "syllables": "",
                "wordFamily": [],
                "exampleEnglish": sentence,
                "exampleChinese": zh,
                "pronounceAs": pronounce_as,
                "documentFrequency": 0,
                "corpusFrequency": 0,
                "reviewStatus": "manually-reviewed-meeting-tier",
                "sourceIds": [],
                "sourceTitle": "Generated meeting-practice sentence",
                "sourceDoi": "",
            }
        )

    existing_word_terms = {
        normalize(item["term"]) for item in items if item["type"] == "word"
    }
    with PRESENTATION_VOCAB.open(encoding="utf-8", newline="") as handle:
        presentation_rows = list(csv.DictReader(handle, delimiter="|"))
    if len(presentation_rows) != 70:
        raise ValueError(
            f"Expected 70 presentation words; got {len(presentation_rows)}"
        )

    presentation_terms = [normalize(row["term"]) for row in presentation_rows]
    duplicate_terms = sorted(
        term for term in presentation_terms if term in existing_word_terms
    )
    if duplicate_terms or len(set(presentation_terms)) != len(presentation_terms):
        raise ValueError(
            "Presentation vocabulary contains duplicate word terms: "
            + ", ".join(duplicate_terms)
        )

    for index, row in enumerate(presentation_rows, start=1):
        term = row["term"].strip()
        source_slides = row["sourceSlides"].strip()
        items.append(
            {
                "id": f"PPT-W{index:03d}",
                "type": "word",
                "tier": "presentation",
                "rank": index,
                "dailyPriority": 0,
                "term": term,
                "displayTerm": term,
                "chinese": row["chinese"].strip(),
                "partOfSpeech": row["partOfSpeech"].strip(),
                "theme": row["theme"].strip(),
                "ipa": row["ipa"].strip(),
                "syllables": hyphenator.inserted(term.lower(), hyphen="·"),
                "wordFamily": [term],
                "exampleEnglish": row["exampleEnglish"].strip(),
                "exampleChinese": row["exampleChinese"].strip(),
                "pronounceAs": row["pronounceAs"].strip() or term,
                "documentFrequency": 0,
                "corpusFrequency": 0,
                "reviewStatus": "manually-reviewed-presentation-tier",
                "sourceType": "presentation",
                "sourceIds": ["PPT-2026-08"],
                "sourceTitle": "Research Progress and Proposed Oxford Visit",
                "sourceDoi": "",
                "sourceSlides": source_slides,
            }
        )

    counts = Counter(item["type"] for item in items)
    expected_counts = {"word": 270, "phrase": 60, "sentence": 40}
    if dict(counts) != expected_counts:
        raise ValueError(f"Unexpected item counts: {dict(counts)}")

    payload = {
        "meta": {
            "version": "2026.08.08-presentation-1",
            "title": "Kessler Research English",
            "targetAuthor": bundle["meta"]["targetAuthor"],
            "orcid": bundle["meta"]["orcid"],
            "publicationCount": len(publications),
            "itemCount": len(items),
            "counts": expected_counts,
            "dailyPlan": {"word": 50, "phrase": 3, "sentence": 2, "reviews": 30},
            "contentPolicy": "Vocabulary is derived from verified paper titles/abstracts and the user's research presentation; examples are paraphrased and abstracts are not republished.",
            "qa": "Paper-derived and presentation-derived items were reviewed; automated source and schema validation applied.",
        },
        "items": items,
    }
    write_text_lf(
        APP_DATA / "learning_items.json",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )
    write_text_lf(
        DATA / "meeting_items.pretty.json",
        json.dumps(payload, ensure_ascii=False, indent=2),
    )

    with (DATA / "meeting_items.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            lineterminator="\n",
            fieldnames=[
                "id",
                "type",
                "rank",
                "dailyPriority",
                "term",
                "chinese",
                "partOfSpeech",
                "theme",
                "ipa",
                "syllables",
                "exampleEnglish",
                "exampleChinese",
                "sourceTitle",
                "sourceDoi",
                "sourceType",
                "sourceSlides",
                "documentFrequency",
                "corpusFrequency",
            ],
        )
        writer.writeheader()
        for item in items:
            writer.writerow({field: item.get(field, "") for field in writer.fieldnames})

    report = [
        "# Meeting-ready Content QA",
        "",
        f"- Total items: {len(items)}",
        f"- Words: {sum(item['type'] == 'word' for item in items)}",
        f"- Phrases: {sum(item['type'] == 'phrase' for item in items)}",
        f"- Scientific communication sentences: {sum(item['type'] == 'sentence' for item in items)}",
        f"- Verified publication corpus: {len(publications)} papers",
        f"- Presentation-derived words: {len(presentation_rows)}",
        f"- Items without corpus source: {len(missing_sources)}",
        "",
        "## Source exceptions",
        "",
    ]
    if missing_sources:
        report.extend(f"- {term}" for term in missing_sources)
    else:
        report.append("- None. Every paper-derived word and phrase maps to at least one verified paper.")
    report.extend(
        [
            "",
            "## Review statement",
            "",
            "- Chinese meanings were selected for the Kessler research context.",
            "- Presentation vocabulary was extracted from the user's English research-progress slides.",
            "- Examples are short learning sentences and are not abstract quotations.",
            "- Special abbreviations have explicit speech text.",
            "- Browser audio remains the authoritative pronunciation playback; IPA is a learning aid.",
            "",
        ]
    )
    write_text_lf(DATA / "meeting_content_qa.md", "\n".join(report))

    print(
        json.dumps(
            {
                "items": len(items),
                "words": counts["word"],
                "phrases": counts["phrase"],
                "sentences": counts["sentence"],
                "presentationWords": len(presentation_rows),
                "missingSources": missing_sources,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
