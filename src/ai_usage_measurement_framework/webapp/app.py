import streamlit as st
import os
import re
import tempfile
import shutil
from datetime import datetime, date
from collections import defaultdict
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError
import requests

st.set_page_config(
    page_title="AI Usage Measurement Framework",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to fix date input visibility
st.markdown("""
<style>
    /* Ensure date input icons are visible */
    .stDateInput svg {
        fill: currentColor !important;
        opacity: 1 !important;
    }
    .stDateInput input {
        color: inherit !important;
    }
    /* Style for the calendar icon */
    [data-testid="stDateInput"] button {
        opacity: 1 !important;
    }
    [data-testid="stDateInput"] button svg {
        fill: currentColor !important;
    }
</style>
""", unsafe_allow_html=True)

# AI-related patterns to detect in commit messages
AI_COMMIT_PATTERNS = [
    # GitHub Copilot patterns
    r"copilot",
    r"github\s*copilot",
    r"co-authored-by:.*copilot",
    r"generated\s*by\s*copilot",
    
    # Windsurf/Codeium patterns
    r"windsurf",
    r"codeium",
    r"cascade",
    
    # General AI patterns
    r"ai[\s-]*generated",
    r"ai[\s-]*assisted",
    r"auto[\s-]*generated",
    r"machine[\s-]*generated",
    r"llm[\s-]*generated",
    r"gpt[\s-]*generated",
    r"claude",
    r"chatgpt",
    r"openai",
    r"anthropic",
    
    # Common AI tool signatures
    r"devin",
    r"cursor",
    r"tabnine",
    r"kite",
    r"codex",
    r"amazon\s*q",
    r"cody",
    
    # AI-assisted commit message patterns
    r"refactor.*ai",
    r"fix.*suggested\s*by",
    r"implement.*generated",
]

TOOL_PATTERNS = {
    "GitHub Copilot": [r"copilot", r"github\s*copilot"],
    "Windsurf": [r"windsurf"],
    "Codeium": [r"codeium"],
    "Cascade": [r"cascade"],
    "Cursor": [r"cursor"],
    "ChatGPT": [r"chatgpt", r"gpt-4", r"gpt-3"],
    "Claude": [r"claude", r"anthropic"],
    "Devin": [r"devin"],
    "Amazon Q": [r"amazon\s*q"],
    "Tabnine": [r"tabnine"],
    "Cody": [r"cody"],
}


def detect_ai_patterns(text: str) -> list[str]:
    """Detect AI-related patterns in text."""
    text_lower = text.lower()
    detected = []
    for pattern in AI_COMMIT_PATTERNS:
        if re.search(pattern, text_lower):
            detected.append(pattern)
    return detected


# GitHub API functions
@st.cache_data(ttl=300)
def get_github_teams(org: str, token: str) -> list[dict]:
    """Fetch teams for a GitHub organization."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    teams = []
    page = 1
    while True:
        resp = requests.get(
            f"https://api.github.com/orgs/{org}/teams",
            headers=headers,
            params={"per_page": 100, "page": page}
        )
        if resp.status_code == 401:
            raise ValueError("Invalid GitHub token. Please check your token and try again.")
        if resp.status_code == 403:
            raise ValueError("Access forbidden. Token may lack 'read:org' scope or org access.")
        if resp.status_code == 404:
            raise ValueError(f"Organization '{org}' not found or not accessible.")
        if resp.status_code != 200:
            raise ValueError(f"GitHub API error: {resp.status_code} - {resp.text}")
        
        data = resp.json()
        if not data:
            break
        teams.extend(data)
        page += 1
    
    return [{"name": t["name"], "slug": t["slug"], "id": t["id"]} for t in teams]


@st.cache_data(ttl=300)
def get_team_repos(org: str, team_slug: str, token: str) -> list[dict]:
    """Fetch repositories for a GitHub team."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    repos = []
    page = 1
    while True:
        resp = requests.get(
            f"https://api.github.com/orgs/{org}/teams/{team_slug}/repos",
            headers=headers,
            params={"per_page": 100, "page": page}
        )
        if resp.status_code != 200:
            raise ValueError(f"Failed to fetch team repos: {resp.status_code}")
        
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    
    return [{"name": r["name"], "full_name": r["full_name"], "clone_url": r["clone_url"], "private": r["private"]} for r in repos]


def extract_ai_tools_from_text(text: str) -> list[str]:
    """Extract specific AI tool names from text."""
    text_lower = text.lower()
    tools = []
    for tool_name, patterns in TOOL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                if tool_name not in tools:
                    tools.append(tool_name)
                break
    return tools


@st.cache_data(ttl=300)
def analyze_git_repo(repo_path: str, branch: str = None, since_date: str = None, until_date: str = None, token: str = None):
    """Analyze a git repository for AI usage patterns."""
    temp_dir = None
    
    try:
        # Handle GitHub URLs
        if repo_path.startswith("http") or repo_path.startswith("git@"):
            temp_dir = tempfile.mkdtemp()
            
            # Add token to URL for private repos
            clone_url = repo_path
            if token and "github.com" in repo_path:
                clone_url = repo_path.replace("https://github.com", f"https://{token}@github.com")
            
            with st.spinner(f"Cloning repository..."):
                repo = Repo.clone_from(clone_url, temp_dir)
            actual_path = temp_dir
            repo_name = repo_path.split("/")[-1].replace(".git", "")
        else:
            actual_path = os.path.expanduser(repo_path)
            repo = Repo(actual_path)
            repo_name = os.path.basename(actual_path)
        
        if branch:
            repo.git.checkout(branch)
        
        # Build commit iterator with date filters
        kwargs = {}
        if since_date:
            kwargs["since"] = since_date
        if until_date:
            kwargs["until"] = until_date
        
        commits = list(repo.iter_commits(**kwargs))
        
        total_commits = len(commits)
        ai_assisted_commits = 0
        commits_by_author = defaultdict(int)
        ai_commits_by_author = defaultdict(int)
        ai_commits_timeline = defaultdict(int)
        all_ai_tools = set()
        sample_ai_commits = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, commit in enumerate(commits):
            if i % 100 == 0:
                progress_bar.progress(min(i / total_commits, 1.0))
                status_text.text(f"Analyzing commit {i+1} of {total_commits}...")
            
            author = commit.author.name if commit.author else "Unknown"
            commits_by_author[author] += 1
            
            # Check commit message for AI patterns
            ai_indicators = detect_ai_patterns(commit.message)
            ai_tools = extract_ai_tools_from_text(commit.message)
            
            if ai_indicators:
                ai_assisted_commits += 1
                ai_commits_by_author[author] += 1
                
                # Group by month for timeline
                month_key = commit.committed_datetime.strftime("%Y-%m")
                ai_commits_timeline[month_key] += 1
                
                all_ai_tools.update(ai_tools)
                
                # Collect sample AI commits (up to 20)
                if len(sample_ai_commits) < 20:
                    try:
                        stats = commit.stats.total
                        files_changed = stats.get("files", 0)
                        insertions = stats.get("insertions", 0)
                        deletions = stats.get("deletions", 0)
                    except Exception:
                        files_changed = 0
                        insertions = 0
                        deletions = 0
                    
                    sample_ai_commits.append({
                        "sha": commit.hexsha[:8],
                        "message": commit.message[:200],
                        "author": author,
                        "date": commit.committed_datetime.isoformat(),
                        "ai_indicators": ai_indicators,
                        "files_changed": files_changed,
                        "insertions": insertions,
                        "deletions": deletions,
                    })
        
        progress_bar.progress(1.0)
        status_text.text("Scanning for Agents.md files...")
        
        # Find and analyze Agents.md files
        agents_md_files = []
        for root, dirs, files in os.walk(actual_path):
            # Skip .git directory
            if ".git" in root:
                continue
            for file in files:
                if file.lower() in ["agents.md", "agent.md", ".agents.md"]:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, actual_path)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        ai_tools = extract_ai_tools_from_text(content)
                        all_ai_tools.update(ai_tools)
                        
                        # Get last modified time
                        mtime = os.path.getmtime(file_path)
                        last_modified = datetime.fromtimestamp(mtime).isoformat()
                        
                        agents_md_files.append({
                            "file_path": rel_path,
                            "content": content[:2000],
                            "ai_tools_mentioned": ai_tools,
                            "last_modified": last_modified,
                        })
                    except Exception:
                        pass
        
        status_text.empty()
        progress_bar.empty()
        
        ai_percentage = (ai_assisted_commits / total_commits * 100) if total_commits > 0 else 0
        
        return {
            "repo_name": repo_name,
            "total_commits": total_commits,
            "ai_assisted_commits": ai_assisted_commits,
            "ai_percentage": round(ai_percentage, 2),
            "commits_by_author": dict(commits_by_author),
            "ai_commits_by_author": dict(ai_commits_by_author),
            "ai_commits_timeline": dict(sorted(ai_commits_timeline.items())),
            "ai_tools_detected": list(all_ai_tools),
            "agents_md_files": agents_md_files,
            "sample_ai_commits": sample_ai_commits,
            "analysis_date": datetime.now().isoformat(),
        }
        
    except InvalidGitRepositoryError:
        st.error(f"Invalid git repository: {repo_path}")
        return None
    except NoSuchPathError:
        st.error(f"Repository path not found: {repo_path}")
        return None
    except Exception as e:
        st.error(f"Error analyzing repository: {str(e)}")
        return None
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def analyze_multiple_repos(repos: list, branch: str = None, since_date: str = None, until_date: str = None, token: str = None):
    """Analyze multiple repositories and aggregate results."""
    all_results = []
    
    progress_container = st.container()
    with progress_container:
        overall_progress = st.progress(0)
        repo_status = st.empty()
    
    for i, repo in enumerate(repos):
        repo_status.text(f"Analyzing {repo['name']} ({i+1}/{len(repos)})...")
        overall_progress.progress((i) / len(repos))
        
        result = analyze_git_repo(
            repo['clone_url'],
            branch=branch,
            since_date=since_date,
            until_date=until_date,
            token=token
        )
        
        if result:
            result['repo_full_name'] = repo.get('full_name', repo['name'])
            all_results.append(result)
    
    overall_progress.progress(1.0)
    repo_status.empty()
    overall_progress.empty()
    
    if not all_results:
        return None
    
    # Aggregate results
    aggregated = {
        "is_multi_repo": True,
        "repos_analyzed": len(all_results),
        "repo_results": all_results,
        "total_commits": sum(r['total_commits'] for r in all_results),
        "ai_assisted_commits": sum(r['ai_assisted_commits'] for r in all_results),
        "ai_percentage": 0,
        "commits_by_author": defaultdict(int),
        "ai_commits_by_author": defaultdict(int),
        "ai_commits_timeline": defaultdict(int),
        "ai_tools_detected": set(),
        "agents_md_files": [],
        "sample_ai_commits": [],
        "analysis_date": datetime.now().isoformat(),
    }
    
    for result in all_results:
        for author, count in result['commits_by_author'].items():
            aggregated['commits_by_author'][author] += count
        for author, count in result['ai_commits_by_author'].items():
            aggregated['ai_commits_by_author'][author] += count
        for month, count in result['ai_commits_timeline'].items():
            aggregated['ai_commits_timeline'][month] += count
        aggregated['ai_tools_detected'].update(result['ai_tools_detected'])
        aggregated['agents_md_files'].extend([
            {**f, 'repo': result['repo_name']} for f in result['agents_md_files']
        ])
        aggregated['sample_ai_commits'].extend([
            {**c, 'repo': result['repo_name']} for c in result['sample_ai_commits'][:5]
        ])
    
    # Convert to regular dicts/lists
    aggregated['commits_by_author'] = dict(aggregated['commits_by_author'])
    aggregated['ai_commits_by_author'] = dict(aggregated['ai_commits_by_author'])
    aggregated['ai_commits_timeline'] = dict(sorted(aggregated['ai_commits_timeline'].items()))
    aggregated['ai_tools_detected'] = list(aggregated['ai_tools_detected'])
    
    if aggregated['total_commits'] > 0:
        aggregated['ai_percentage'] = round(
            aggregated['ai_assisted_commits'] / aggregated['total_commits'] * 100, 2
        )
    
    return aggregated


def render_single_repo_details(repo_result, expanded=False):
    """Render detailed view for a single repository in drill-down mode."""
    repo_name = repo_result.get('repo_full_name', repo_result['repo_name'])
    
    with st.expander(f"📁 **{repo_name}** - {repo_result['ai_assisted_commits']} AI commits ({repo_result['ai_percentage']}%)", expanded=expanded):
        # Metrics for this repo
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Commits", f"{repo_result['total_commits']:,}")
        with col2:
            st.metric("AI-Assisted", f"{repo_result['ai_assisted_commits']:,}")
        with col3:
            st.metric("AI %", f"{repo_result['ai_percentage']}%")
        with col4:
            tools = ", ".join(repo_result['ai_tools_detected']) if repo_result['ai_tools_detected'] else "None"
            st.metric("Tools", len(repo_result['ai_tools_detected']))
            if repo_result['ai_tools_detected']:
                st.caption(tools)
        
        # Sub-tabs for this repo's details
        sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
            "📊 Charts", "👥 Authors", "💻 AI Commits", "📄 Agents.md"
        ])
        
        with sub_tab1:
            col1, col2 = st.columns(2)
            with col1:
                # Pie chart
                pie_data = pd.DataFrame({
                    "Type": ["AI-Assisted", "Regular"],
                    "Count": [repo_result['ai_assisted_commits'], 
                             repo_result['total_commits'] - repo_result['ai_assisted_commits']]
                })
                fig = px.pie(pie_data, values="Count", names="Type", 
                           color_discrete_sequence=["#8884d8", "#82ca9d"],
                           title="AI vs Regular Commits")
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Timeline
                if repo_result['ai_commits_timeline']:
                    timeline_data = pd.DataFrame(
                        list(repo_result['ai_commits_timeline'].items()),
                        columns=["Month", "Commits"]
                    )
                    fig = px.line(timeline_data, x="Month", y="Commits", markers=True,
                                 title="AI Commits Over Time")
                    fig.update_traces(line_color="#8884d8")
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No timeline data available")
        
        with sub_tab2:
            if repo_result['ai_commits_by_author']:
                author_data = []
                for author, ai_count in sorted(repo_result['ai_commits_by_author'].items(), 
                                               key=lambda x: x[1], reverse=True):
                    total = repo_result['commits_by_author'].get(author, 0)
                    pct = (ai_count / total * 100) if total > 0 else 0
                    author_data.append({
                        "Author": author,
                        "Total Commits": total,
                        "AI-Assisted": ai_count,
                        "AI %": f"{pct:.1f}%"
                    })
                st.dataframe(pd.DataFrame(author_data), use_container_width=True, hide_index=True)
            else:
                st.info("No AI-assisted commits by authors")
        
        with sub_tab3:
            if repo_result['sample_ai_commits']:
                for commit in repo_result['sample_ai_commits'][:10]:
                    st.markdown(f"**{commit['sha']}** - {commit['author']} ({commit['date'][:10]})")
                    st.code(commit['message'][:300], language=None)
                    st.caption(f"Patterns: {', '.join(commit['ai_indicators'])} | Changes: +{commit['insertions']} -{commit['deletions']}")
                    st.markdown("---")
            else:
                st.info("No AI-assisted commits found")
        
        with sub_tab4:
            if repo_result['agents_md_files']:
                for f in repo_result['agents_md_files']:
                    st.markdown(f"**{f['file_path']}** (Modified: {f['last_modified'][:10]})")
                    if f['ai_tools_mentioned']:
                        st.caption(f"Tools: {', '.join(f['ai_tools_mentioned'])}")
                    st.code(f['content'][:1000], language="markdown")
            else:
                st.info("No Agents.md files found")


def render_results(result):
    """Render analysis results."""
    is_multi = result.get('is_multi_repo', False)
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if is_multi:
            st.metric(
                label="Repositories Analyzed",
                value=f"{result['repos_analyzed']:,}",
            )
        else:
            st.metric(
                label="Total Commits",
                value=f"{result['total_commits']:,}",
                help=f"Repository: {result.get('repo_name', 'N/A')}"
            )
    
    with col2:
        if is_multi:
            st.metric(
                label="Total Commits",
                value=f"{result['total_commits']:,}",
            )
        else:
            st.metric(
                label="AI-Assisted Commits",
                value=f"{result['ai_assisted_commits']:,}",
                delta=f"{result['ai_percentage']}%"
            )
    
    with col3:
        if is_multi:
            st.metric(
                label="AI-Assisted Commits",
                value=f"{result['ai_assisted_commits']:,}",
                delta=f"{result['ai_percentage']}%"
            )
        else:
            st.metric(
                label="Contributors",
                value=len(result['commits_by_author']),
                help=f"{len(result['ai_commits_by_author'])} using AI tools"
            )
    
    with col4:
        st.metric(
            label="AI Tools Detected",
            value=len(result['ai_tools_detected'])
        )
        if result['ai_tools_detected']:
            st.caption(", ".join(result['ai_tools_detected']))
    
    st.divider()
    
    # Tabs for different views
    if is_multi:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Overall Summary",
            "🔍 Drill-Down by Repository",
            "📈 Timeline",
            "👥 Authors",
            "💻 AI Commits",
            "📄 Agents.md Files"
        ])
    else:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview",
            "📈 Timeline",
            "👥 Authors",
            "💻 AI Commits",
            "📄 Agents.md Files"
        ])
        tab6 = None
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("AI vs Regular Commits")
            pie_data = pd.DataFrame({
                "Type": ["AI-Assisted", "Regular"],
                "Count": [result['ai_assisted_commits'], result['total_commits'] - result['ai_assisted_commits']]
            })
            fig = px.pie(pie_data, values="Count", names="Type", 
                       color_discrete_sequence=["#8884d8", "#82ca9d"])
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Top Contributors (by commits)")
            author_data = sorted(result['commits_by_author'].items(), key=lambda x: x[1], reverse=True)[:10]
            df = pd.DataFrame(author_data, columns=["Author", "Total Commits"])
            df["AI-Assisted"] = df["Author"].apply(lambda x: result['ai_commits_by_author'].get(x, 0))
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Total Commits", x=df["Total Commits"], y=df["Author"], orientation='h', marker_color="#8884d8"))
            fig.add_trace(go.Bar(name="AI-Assisted", x=df["AI-Assisted"], y=df["Author"], orientation='h', marker_color="#82ca9d"))
            fig.update_layout(barmode='group', yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
    
    if is_multi and tab6:
        with tab2:
            st.subheader("Drill-Down: Individual Repository Details")
            st.markdown("Click on any repository below to expand and view detailed metrics, charts, authors, and AI commits for that specific repository.")
            
            # Summary table at the top
            st.markdown("#### Quick Summary")
            repo_data = []
            for repo_result in result['repo_results']:
                repo_data.append({
                    "Repository": repo_result.get('repo_full_name', repo_result['repo_name']),
                    "Total Commits": repo_result['total_commits'],
                    "AI-Assisted": repo_result['ai_assisted_commits'],
                    "AI %": f"{repo_result['ai_percentage']}%",
                    "Tools": ", ".join(repo_result['ai_tools_detected']) or "None"
                })
            st.dataframe(pd.DataFrame(repo_data), use_container_width=True, hide_index=True)
            
            # Bar chart by repo
            st.markdown("#### AI-Assisted Commits by Repository")
            repo_chart_data = pd.DataFrame([
                {"Repository": r['repo_name'], "AI-Assisted Commits": r['ai_assisted_commits']}
                for r in result['repo_results']
            ])
            fig = px.bar(repo_chart_data, x="Repository", y="AI-Assisted Commits", color_discrete_sequence=["#8884d8"])
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### Detailed Repository Reports")
            st.markdown("Expand each repository below to see full details including charts, author breakdown, AI commits, and Agents.md files.")
            
            # Sort repos by AI commits (highest first) for better UX
            sorted_repos = sorted(result['repo_results'], 
                                 key=lambda x: x['ai_assisted_commits'], reverse=True)
            
            # Render each repo with drill-down capability
            for i, repo_result in enumerate(sorted_repos):
                # Expand the first repo by default if it has AI commits
                expand_first = (i == 0 and repo_result['ai_assisted_commits'] > 0)
                render_single_repo_details(repo_result, expanded=expand_first)
        
        timeline_tab = tab3
        authors_tab = tab4
        commits_tab = tab5
        agents_tab = tab6
    else:
        timeline_tab = tab2
        authors_tab = tab3
        commits_tab = tab4
        agents_tab = tab5
    
    with timeline_tab:
        st.subheader("AI-Assisted Commits Over Time")
        if result['ai_commits_timeline']:
            timeline_data = pd.DataFrame(
                list(result['ai_commits_timeline'].items()),
                columns=["Month", "Commits"]
            )
            fig = px.line(timeline_data, x="Month", y="Commits", markers=True)
            fig.update_traces(line_color="#8884d8")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No AI-assisted commits found in the timeline")
    
    with authors_tab:
        st.subheader("Contributors with AI-Assisted Commits")
        if result['ai_commits_by_author']:
            author_ai_data = []
            for author, ai_count in sorted(result['ai_commits_by_author'].items(), key=lambda x: x[1], reverse=True):
                total_count = result['commits_by_author'].get(author, 0)
                percentage = (ai_count / total_count * 100) if total_count > 0 else 0
                author_ai_data.append({
                    "Author": author,
                    "Total Commits": total_count,
                    "AI-Assisted": ai_count,
                    "AI %": f"{percentage:.1f}%"
                })
            
            st.dataframe(pd.DataFrame(author_ai_data), use_container_width=True, hide_index=True)
        else:
            st.info("No contributors with AI-assisted commits found")
    
    with commits_tab:
        st.subheader("Sample AI-Assisted Commits")
        st.caption("Commits detected with AI-related patterns in their messages")
        
        if result['sample_ai_commits']:
            for commit in result['sample_ai_commits']:
                repo_prefix = f"[{commit.get('repo', '')}] " if commit.get('repo') else ""
                with st.expander(f"**{repo_prefix}{commit['sha']}** - {commit['author']} ({commit['date'][:10]})"):
                    st.markdown(f"```\n{commit['message']}\n```")
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown("**Detected patterns:** " + ", ".join([f"`{p}`" for p in commit['ai_indicators']]))
                    with col2:
                        st.markdown(f"**Changes:** +{commit['insertions']} -{commit['deletions']} ({commit['files_changed']} files)")
        else:
            st.info("No AI-assisted commits found")
    
    with agents_tab:
        st.subheader("Agents.md Files")
        st.caption("Documentation files that describe AI tool usage in the repository")
        
        if result['agents_md_files']:
            for file in result['agents_md_files']:
                repo_prefix = f"[{file.get('repo', '')}] " if file.get('repo') else ""
                with st.expander(f"📄 **{repo_prefix}{file['file_path']}** (Modified: {file['last_modified'][:10]})"):
                    if file['ai_tools_mentioned']:
                        st.markdown("**AI Tools Mentioned:** " + ", ".join(file['ai_tools_mentioned']))
                    st.code(file['content'], language="markdown")
        else:
            st.info("No Agents.md files found in the repository")
    
    st.divider()
    st.caption(f"Analysis performed on {result['analysis_date'][:19].replace('T', ' ')}")


def main():
    st.title("🤖 AI Usage Measurement Framework")
    st.markdown("Analyze AI-assisted development in your repositories")
    
    # Initialize session state
    if "github_token" not in st.session_state:
        st.session_state.github_token = os.environ.get("GITHUB_TOKEN", "")
    
    # Sidebar for input
    with st.sidebar:
        st.header("Analysis Mode")
        
        analysis_mode = st.radio(
            "Select analysis mode",
            ["Single Repository", "GitHub Team"],
            horizontal=False,
            help="Analyze a single repo or all repos under a GitHub team"
        )
        
        st.divider()
        
        # Variables to track state
        analyze_button = False
        repo_path = ""
        branch = ""
        since_date = None
        until_date = None
        github_token = ""
        team_repos = []
        
        if analysis_mode == "Single Repository":
            st.header("Repository Settings")
            
            repo_path = st.text_input(
                "Repository Path or URL",
                placeholder="/path/to/repo or https://github.com/user/repo",
                help="Enter a local path or GitHub URL"
            )
            
            branch = st.text_input(
                "Branch (optional)",
                placeholder="main",
                help="Leave empty for default branch"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                since_date = st.date_input(
                    "📅 Since Date",
                    value=None,
                    help="Filter commits from this date"
                )
            with col2:
                until_date = st.date_input(
                    "📅 Until Date",
                    value=None,
                    help="Filter commits until this date"
                )
            
            # Optional token for private repos
            with st.expander("🔐 GitHub Token (for private repos)"):
                github_token = st.text_input(
                    "Personal Access Token",
                    type="password",
                    value=st.session_state.github_token,
                    help="Required for private repositories",
                    key="single_repo_token"
                )
            
            analyze_button = st.button("🔍 Analyze Repository", type="primary", use_container_width=True)
            
        else:  # GitHub Team mode
            st.header("GitHub Team Settings")
            
            github_org = st.text_input(
                "GitHub Organization",
                placeholder="your-org-name",
                help="The GitHub organization name"
            )
            
            github_token = st.text_input(
                "🔐 GitHub Personal Access Token",
                type="password",
                value=st.session_state.github_token,
                help="Token needs 'read:org' and 'repo' scopes",
                key="team_token"
            )
            
            teams = []
            selected_team = None
            
            if github_org and github_token:
                try:
                    with st.spinner("Loading teams..."):
                        teams = get_github_teams(github_org, github_token)
                    
                    if teams:
                        team_names = [t['name'] for t in teams]
                        selected_team_name = st.selectbox(
                            "Select Team",
                            options=team_names,
                            help="Select a team to analyze its repositories"
                        )
                        selected_team = next((t for t in teams if t['name'] == selected_team_name), None)
                        
                        if selected_team:
                            with st.spinner("Loading team repositories..."):
                                team_repos = get_team_repos(github_org, selected_team['slug'], github_token)
                            
                            st.success(f"Found {len(team_repos)} repositories in team '{selected_team_name}'")
                            
                            analyze_all = st.checkbox("Analyze all repositories", value=True)
                            
                            if not analyze_all:
                                repo_names = [r['name'] for r in team_repos]
                                selected_repos = st.multiselect(
                                    "Select specific repositories",
                                    options=repo_names,
                                    default=repo_names[:5] if len(repo_names) > 5 else repo_names
                                )
                                team_repos = [r for r in team_repos if r['name'] in selected_repos]
                    else:
                        st.warning("No teams found in this organization")
                        
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error loading teams: {str(e)}")
            
            branch = st.text_input(
                "Branch (optional)",
                placeholder="main",
                help="Leave empty for default branch"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                since_date = st.date_input(
                    "📅 Since Date",
                    value=None,
                    help="Filter commits from this date",
                    key="team_since"
                )
            with col2:
                until_date = st.date_input(
                    "📅 Until Date",
                    value=None,
                    help="Filter commits until this date",
                    key="team_until"
                )
            
            analyze_button = st.button(
                f"🔍 Analyze {len(team_repos)} Repositories" if team_repos else "🔍 Analyze",
                type="primary",
                use_container_width=True,
                disabled=not team_repos
            )
        
        st.divider()
        
        st.header("AI Patterns Detected")
        st.markdown("""
        **Tools Detected:**
        - GitHub Copilot
        - Windsurf / Codeium
        - Cursor
        - ChatGPT / Claude
        - Devin
        - Amazon Q
        - Tabnine / Cody
        """)
    
    # Main content - handle analysis
    if analysis_mode == "Single Repository":
        if analyze_button and repo_path:
            since_str = since_date.isoformat() if since_date else None
            until_str = until_date.isoformat() if until_date else None
            token = github_token if github_token else None
            
            result = analyze_git_repo(repo_path, branch or None, since_str, until_str, token)
            
            if result:
                st.session_state["result"] = result
    else:  # GitHub Team mode
        if analyze_button and team_repos:
            since_str = since_date.isoformat() if since_date else None
            until_str = until_date.isoformat() if until_date else None
            
            result = analyze_multiple_repos(
                team_repos,
                branch=branch or None,
                since_date=since_str,
                until_date=until_str,
                token=github_token
            )
            
            if result:
                st.session_state["result"] = result
    
    # Display results
    if "result" in st.session_state:
        render_results(st.session_state["result"])
    else:
        # Empty state
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 50px;">
                <h3>🔍 No Repository Analyzed</h3>
                <p>Enter a repository path in the sidebar to analyze AI usage patterns.</p>
                <p>Or select a GitHub team to analyze all repositories under that team.</p>
                <p>The tool will scan commit messages and Agents.md files to detect AI-assisted development.</p>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
