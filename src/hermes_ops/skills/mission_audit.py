from __future__ import annotations

import ast
import json
from pathlib import PurePosixPath
import re
import unicodedata
from typing import Any

from hermes_ops.core.errors import SkillExecutionError
from hermes_ops.core.results import Status
from hermes_ops.skills.controlled_reader import SourceDocument, read_source_documents, validate_target
from hermes_ops.skills.execution_models import SkillExecutionEvidence, SkillExecutionResult, SkillExecutionStatus
from hermes_ops.skills.mission_models import EvidenceFile, EvidenceRegion, EvidenceRelationship, EvidenceSymbol, MissionCompleteness, MissionEvidencePack, RelatedTest, SelectionTerm

MAX_TERMS=24; MAX_SYMBOLS=10_000; MAX_FILES=100; MAX_REGIONS_PER_FILE=12; MAX_REGIONS=300; MAX_PACK_SYMBOLS=300; MAX_RELATIONSHIPS=500; MAX_TESTS=100; MAX_JSON_BYTES=2*1024*1024
STOPWORDS=frozenset("a an and as at audit auditar analyze analisar examine examinar de da das do dos e em for from in investigar mission missão o os para por review revisar the to um uma verificar with com fluxo processo sobre código code".split())
TOKEN=re.compile(r"[^\W_][\w]*", re.UNICODE)
DEFINITION=re.compile(r"^\s*(?:class|def|async\s+def|function|const|let|var)\s+([A-Za-z_$][\w$]*)", re.MULTILINE)
IMPORT=re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+)|.*?from\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+))", re.MULTILINE)


def _fail(code:str,message:str)->None: raise SkillExecutionError(code,message)
def _fold(value:str)->str: return "".join(c for c in unicodedata.normalize("NFKD",value.casefold()) if not unicodedata.combining(c))


def normalize_mission(value:Any)->tuple[str,tuple[SelectionTerm,...]]:
    if type(value) is not str or "\0" in value or any(ord(c)<32 and not c.isspace() for c in value): _fail("SKILL_EXECUTION_INVALID","Mission must be valid text")
    mission=" ".join(unicodedata.normalize("NFKC",value).split())
    if not 3<=len(mission)<=500: _fail("SKILL_EXECUTION_INVALID","Mission length must be between 3 and 500 characters")
    raw=[t.casefold() for t in TOKEN.findall(mission)]
    terms=[]
    for token in raw:
        folded=_fold(token)
        if len(token)<3 or token in STOPWORDS or folded in STOPWORDS: continue
        if token not in terms: terms.append(token)
        if folded!=token and folded not in terms: terms.append(folded)
    if len(terms)>MAX_TERMS: _fail("MISSION_TERM_LIMIT_EXCEEDED","Mission has too many significant terms")
    return mission,tuple(SelectionTerm(t,"accent_alias" if _fold(t)==t and t not in raw else "mission") for t in terms)


def _roles(path:str)->tuple[str,...]:
    lower=path.casefold(); parts=set(TOKEN.findall(lower)); roles=[]
    test=PurePosixPath(path).name.startswith("test_") or "/tests/" in f"/{lower}" or ".test." in lower or lower.endswith("_test.py")
    if test: roles.append("test")
    if parts & {"service"}: roles.append("service")
    if parts & {"repository","repo","dao"}: roles.append("repository")
    if parts & {"persistence","storage","database","store"}: roles.append("persistence")
    roles.append("implementation" if not test else "support")
    return tuple(sorted(set(roles)))


def _lines(document:SourceDocument, terms:tuple[str,...]):
    result=[]
    for number,line in enumerate(document.text.splitlines(),1):
        folded=_fold(line); hits=tuple(t for t in terms if _fold(t) in folded)
        if hits:
            stripped=line.strip(); kind="comment" if stripped.startswith(("#","//","/*","*")) else "docstring" if stripped.startswith(('"""',"'''")) else "active_code"
            result.append((number,line,hits,kind))
    return result


def _symbols(document:SourceDocument)->tuple[tuple[str,str,int],...]:
    values=[]
    for match in DEFINITION.finditer(document.text):
        line=document.text.count("\n",0,match.start())+1; prefix=match.group(0).lstrip()
        kind="class" if prefix.startswith("class") else "function" if prefix.startswith(("def","async","function")) else "variable"
        values.append((match.group(1),kind,line))
    return tuple(values)


def _imports(document: SourceDocument) -> tuple[tuple[str, int], ...]:
    """Return literal module references with their source line; never import them."""
    found: list[tuple[str, int]] = []
    if PurePosixPath(document.path).suffix in {".py", ".pyi"}:
        try:
            tree = ast.parse(document.text)
        except (SyntaxError, ValueError, RecursionError):
            tree = None
        if tree is not None:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    found.extend((alias.name, node.lineno) for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    prefix = "." * node.level + (node.module or "")
                    for alias in node.names:
                        module = f"{prefix}.{alias.name}" if node.module else f"{prefix}{alias.name}"
                        found.append((module, node.lineno))
    else:
        for match in IMPORT.finditer(document.text):
            module = next((group for group in match.groups() if group), "")
            if module:
                found.append((module, document.text.count("\n", 0, match.start()) + 1))
    return tuple(sorted(set(found), key=lambda item: (item[1], item[0])))


def _module_index(documents: tuple[SourceDocument, ...]) -> dict[str, tuple[str, ...]]:
    index: dict[str, list[str]] = {}
    for document in documents:
        path = PurePosixPath(document.path)
        stemmed = path.with_suffix("").as_posix()
        keys = {stemmed}
        if path.stem == "__init__":
            keys.add(path.parent.as_posix())
        for key in keys:
            index.setdefault(key, []).append(document.path)
    return {key: tuple(sorted(values)) for key, values in index.items()}


def _resolve_internal_import(source: str, module: str, index: dict[str, tuple[str, ...]]) -> str | None:
    source_parent = PurePosixPath(source).parent
    candidates: list[str] = []
    if module.startswith("."):
        level = len(module) - len(module.lstrip("."))
        base = source_parent
        for _ in range(max(0, level - 1)):
            base = base.parent
        remainder = module[level:].replace(".", "/")
        candidates.append((base / remainder).as_posix())
    elif module.startswith(("./", "../")):
        parts = list(source_parent.parts)
        for part in PurePosixPath(module).parts:
            if part == "..":
                if parts: parts.pop()
            elif part != ".": parts.append(part)
        candidates.append(PurePosixPath(*parts).with_suffix("").as_posix())
    else:
        candidates.append(module.replace(".", "/"))
    # ``from package.module import Symbol`` and ``from package import module``
    # are syntactically indistinguishable without importing the package. Try
    # the most specific literal path first, then its literal parents only.
    expanded: list[str] = []
    for candidate in candidates:
        parts = PurePosixPath(candidate).parts
        expanded.extend(PurePosixPath(*parts[:end]).as_posix() for end in range(len(parts), 0, -1))
    for candidate in expanded:
        matches = index.get(candidate, ())
        if len(matches) == 1:
            return matches[0]
    return None


def _relationship_line(relationship: EvidenceRelationship) -> tuple[str, int] | None:
    try:
        path, line_text = relationship.evidence_region.rsplit(":", 1)
        line = int(line_text)
    except (AttributeError, ValueError):
        return None
    return (path, line) if path and line >= 1 else None


def _select_regions(
    candidates: list[EvidenceRegion],
    relationships: list[EvidenceRelationship],
) -> tuple[list[EvidenceRegion], bool]:
    """Select regions while keeping structural provenance inside closed caps."""
    unique = {(region.path, region.start_line, region.end_line): region for region in candidates}
    required = {
        locator
        for relationship in relationships
        if (locator := _relationship_line(relationship)) is not None
    }
    ordered = sorted(
        unique.values(),
        key=lambda region: (
            0 if (region.path, region.start_line) in required and region.start_line == region.end_line else 1,
            region.path,
            region.start_line,
            region.end_line,
        ),
    )
    selected: list[EvidenceRegion] = []
    per_file: dict[str, int] = {}
    for region in ordered:
        if per_file.get(region.path, 0) >= MAX_REGIONS_PER_FILE or len(selected) >= MAX_REGIONS:
            continue
        selected.append(region)
        per_file[region.path] = per_file.get(region.path, 0) + 1
    selected.sort(key=lambda region: (region.path, region.start_line, region.end_line))
    return selected, len(selected) < len(unique)


def build_evidence_pack(target:Any, mission_value:Any)->MissionEvidencePack:
    mission, initial=normalize_mission(mission_value); inventory=read_source_documents(target); direct=tuple(t.term for t in initial)
    indexed=sum(len(_symbols(d)) for d in inventory.documents)
    if indexed>MAX_SYMBOLS: _fail("MISSION_SYMBOL_INDEX_LIMIT_EXCEEDED","Mission symbol index limit exceeded")
    file_rows=[]; regions=[]; symbols=[]; relationships=[]; tests=[]; counts={t:0 for t in direct}; limitations=[]
    direct_paths=[]; documents={document.path:document for document in inventory.documents}; analyses={}
    for document in inventory.documents:
        rows=_lines(document,direct); pathhits=tuple(t for t in direct if _fold(t) in _fold(document.path)); defs=_symbols(document)
        symhits=tuple(t for t in direct if any(_fold(t) in _fold(s[0]) for s in defs))
        imports=_imports(document)
        importhits=tuple(t for t in direct if any(_fold(t) in _fold(i[0]) for i in imports))
        activehits=tuple(sorted({t for _,_,hs,k in rows if k=="active_code" for t in hs})); commenthits=tuple(sorted({t for _,_,hs,k in rows if k!="active_code" for t in hs}))
        hitset=set(pathhits+symhits+importhits+activehits+commenthits)
        for term in hitset: counts[term]+=1
        if not hitset: continue
        analyses[document.path]=(rows,defs,imports)
        direct_paths.append(document.path); score=12*len(pathhits)+10*len(symhits)+8*len(importhits)+6*len(activehits)+4*len(commenthits)
        reasons=tuple(sorted({*(f"path:{t}" for t in pathhits),*(f"symbol:{t}" for t in symhits),*(f"import:{t}" for t in importhits),*(f"identifier:{t}" for t in activehits),*(f"comment:{t}" for t in commenthits)}))
        file_rows.append(EvidenceFile(document.path,_roles(document.path),score,reasons))
        for number,line,hits,kind in rows[:MAX_REGIONS_PER_FILE]:
            regions.append(EvidenceRegion(document.path,number,number,line.strip()[:2000],kind,tuple(f"term:{t}" for t in hits)))
        for name,kind,line in defs:
            if any(_fold(t) in _fold(name) for t in direct): symbols.append(EvidenceSymbol(name,kind,document.path,f"{document.path}:{line}",(f"mission term in {kind}",)))
        if "test" in _roles(document.path): tests.append(RelatedTest(document.path,tuple(sorted(set(direct_paths[:-1]))),("test naming convention",)))
    # The direct set is frozen before this pass: targets may be added, but their
    # imports are deliberately never traversed (the closed one-hop contract).
    index=_module_index(inventory.documents); selected=set(direct_paths); region_keys={(r.path,r.start_line,r.end_line) for r in regions}
    for source in tuple(sorted(direct_paths)):
        _,_,imports=analyses[source]
        source_lines=documents[source].text.splitlines()
        for imported,line in imports:
            target_path=_resolve_internal_import(source,imported,index)
            if target_path is None or target_path == source: continue
            locator=f"{source}:{line}"
            relationships.append(EvidenceRelationship("import",source,target_path,locator,f"literal internal import {imported}"))
            if (source,line,line) not in region_keys and line <= len(source_lines):
                regions.append(EvidenceRegion(source,line,line,source_lines[line-1].strip()[:2000],"active_code",(f"structural import to {target_path}",)))
                region_keys.add((source,line,line))
            if target_path not in selected:
                selected.add(target_path); target_document=documents[target_path]
                file_rows.append(EvidenceFile(target_path,_roles(target_path),7,(f"import seed from {locator}",)))
                target_lines=target_document.text.splitlines()
                context=[]
                for name,kind,target_line in _symbols(target_document):
                    symbols.append(EvidenceSymbol(name,kind,target_path,f"{target_path}:{target_line}",(f"one-hop import from {locator}",)))
                    if target_line <= len(target_lines): context.append((target_line,target_lines[target_line-1]))
                if not context and target_lines: context=[(1,target_lines[0])]
                for target_line,text in context[:MAX_REGIONS_PER_FILE]:
                    if (target_path,target_line,target_line) not in region_keys:
                        regions.append(EvidenceRegion(target_path,target_line,target_line,text.strip()[:2000],"active_code",(f"one-hop import from {locator}",)))
                        region_keys.add((target_path,target_line,target_line))
    file_rows.sort(key=lambda f:(-f.score,f.path))
    file_cap_reached=len(file_rows)>MAX_FILES
    file_rows=file_rows[:MAX_FILES]
    selected_paths={item.path for item in file_rows}
    regions,region_cap_reached=_select_regions(regions,relationships)
    regions=[region for region in regions if region.path in selected_paths]
    region_keys={(region.path,region.start_line,region.end_line) for region in regions}
    relationship_candidates=sorted(relationships,key=lambda r:(r.kind,r.source,r.target,r.evidence_region,r.reason))
    relationships=[]
    for relationship in relationship_candidates:
        locator=_relationship_line(relationship)
        if locator is None or relationship.source not in selected_paths or relationship.target not in selected_paths:
            continue
        path,line=locator
        if not any(region_path==path and start<=line<=end for region_path,start,end in region_keys):
            continue
        relationships.append(relationship)
    relationship_provenance_omitted=len(relationships)<len(relationship_candidates)
    relationship_cap_reached=len(relationships)>MAX_RELATIONSHIPS
    relationships=relationships[:MAX_RELATIONSHIPS]
    symbol_candidates=[symbol for symbol in symbols if symbol.path in selected_paths]
    symbol_cap_reached=len(symbol_candidates)>MAX_PACK_SYMBOLS
    symbols=sorted(symbol_candidates,key=lambda s:(s.path,s.region,s.name))[:MAX_PACK_SYMBOLS]
    test_candidates=[test for test in tests if test.path in selected_paths]
    test_cap_reached=len(test_candidates)>MAX_TESTS
    tests=sorted(test_candidates,key=lambda t:t.path)[:MAX_TESTS]
    omitted=any((file_cap_reached,region_cap_reached,symbol_cap_reached,relationship_cap_reached,test_cap_reached,relationship_provenance_omitted))
    if omitted: limitations.append("SELECTION_CAP_REACHED")
    matched=tuple(sorted(t for t,c in counts.items() if c)); unmatched=tuple(sorted(t for t,c in counts.items() if not c)); active=any(r.content_kind=="active_code" for r in regions); related=bool(relationships); has_test=bool(tests)
    central=tuple(t.term for t in initial if t.source=="mission"); uncovered_central=tuple(t for t in central if not counts[t]); central_covered=not uncovered_central
    sufficient=len(matched)>=2 and central_covered and active and related and has_test and not omitted
    codes=[]
    if len(matched)<2: codes.append("INSUFFICIENT_DIRECT_TERMS")
    if not central_covered: codes.append("UNCOVERED_CENTRAL_TERMS")
    if not active: codes.append("NO_ACTIVE_IMPLEMENTATION")
    if not related: codes.append("NO_TRACEABLE_RELATIONSHIP")
    if not has_test: codes.append("NO_RELATED_TEST")
    if omitted: codes.append("CAP_OMISSION")
    terms=tuple(SelectionTerm(t.term,t.source,t.derived_from,counts[t.term]) for t in initial)
    completeness=MissionCompleteness("sufficient" if sufficient else "insufficient",matched,unmatched,active,related,has_test,(("files",len(file_rows)),("regions",len(regions)),("symbols",len(symbols)),("relationships",len(relationships)),("tests",len(tests))),tuple(codes))
    pack=MissionEvidencePack(1,mission,"<PROJECT_ROOT>",terms,tuple(file_rows),tuple(regions),tuple(symbols),tuple(relationships),tuple(tests),tuple(codes[:24]),completeness,tuple(limitations[:24]))
    if len(json.dumps(pack,default=lambda o:{f:getattr(o,f) for f in o.__dataclass_fields__},ensure_ascii=False).encode())>MAX_JSON_BYTES: _fail("MISSION_EVIDENCE_PACK_SIZE_EXCEEDED","Mission evidence pack exceeds its serialized size limit")
    return pack


def run_mission_audit(target:Any, mission:Any)->SkillExecutionResult:
    pack=build_evidence_pack(target,mission); sufficient=pack.completeness.status=="sufficient"
    evidence=SkillExecutionEvidence("mission_evidence_pack",Status.OK if sufficient else Status.WARNING,"Mission evidence collection completed.",pack,"ok" if sufficient else "MISSION_INSUFFICIENT_EVIDENCE")
    return SkillExecutionResult("mission-audit",SkillExecutionStatus.PASSED if sufficient else SkillExecutionStatus.COMPLETED_WITH_INSUFFICIENT_EVIDENCE,0 if sufficient else 3,(evidence,))
