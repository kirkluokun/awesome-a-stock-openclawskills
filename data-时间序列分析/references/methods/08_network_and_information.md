# 08 — 网络与信息论 (Network & Information Theory)

将资产间的关系可视化为网络结构，发现隐藏的聚类和信息传导路径。

---

## 方法一览

| 方法       | 函数                                 | 输出            |
| ---------- | ------------------------------------ | --------------- |
| 相关性网络 | `correlation_network(df, threshold)` | 网络图 + 中心性 |
| 最小生成树 | `build_mst(df)`                      | 核心关系骨架    |
| 社区检测   | `community_detection(df)`            | 自动聚类分组    |
| 互信息     | `mutual_information(a, b)`           | 非线性相关度量  |

---

## 相关性网络

将资产两两相关关系构建为网络图：

```python
from analysis_toolkit import correlation_network

result = correlation_network(returns_df, threshold=0.3)

# 基本信息
print(f"网络中心(Hub): {result['hub']}")
print(f"度中心性: {result['degree_centrality']}")

# 可视化
import networkx as nx
import matplotlib.pyplot as plt

G = result['graph']
fig, ax = plt.subplots(figsize=(12, 10))

pos = nx.spring_layout(G, k=2, seed=42)
centrality = result['degree_centrality']
node_sizes = [centrality.get(n, 0) * 3000 + 300 for n in G.nodes()]
edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
edge_colors = ['green' if w > 0 else 'red' for w in edge_weights]

nx.draw(G, pos, ax=ax, with_labels=True, node_size=node_sizes,
        node_color='lightblue', edge_color=edge_colors,
        width=[abs(w)*3 for w in edge_weights],
        font_size=9, font_weight='bold')
ax.set_title('资产相关性网络')
```

### threshold 选择
| threshold | 效果                   |
| --------- | ---------------------- |
| 0.3       | 显示弱相关以上，网络密 |
| **0.5**   | 推荐默认，中等密度     |
| 0.7       | 只显示强相关，网络稀疏 |

---

## 最小生成树 (MST)

提取最核心的N-1条边，简化复杂网络：

```python
from analysis_toolkit import build_mst

result = build_mst(returns_df)

# 可视化
G = result['mst_graph']
fig, ax = plt.subplots(figsize=(14, 10))
pos = nx.spring_layout(G, k=3, seed=42)
nx.draw(G, pos, ax=ax, with_labels=True,
        node_color='lightcoral', node_size=800,
        edge_color='gray', width=2, font_size=10)

# 标注边的距离
edge_labels = {(u, v): f"{d['weight']:.2f}" for u, v, d in G.edges(data=True)}
nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=7)
ax.set_title('最小生成树 (MST)')
```

### MST 的解读
- **中心节点**（度数高的节点）= 市场中的"核心驱动者"
- **叶子节点** = 相对独立的资产
- **边越短（距离小）** = 两个资产越相似
- **同一分支上的资产** = 可能属于同一板块/主题

---

## 社区检测

自动发现资产的聚类分组：

```python
from analysis_toolkit import community_detection

result = community_detection(returns_df)

print(f"发现 {result['n_communities']} 个社区")
print(f"模块度: {result['modularity']:.3f}")

for i, community in enumerate(result['communities']):
    print(f"  社区 {i+1}: {community}")

# 想象一下输出：
# 社区 1: ['AAPL', 'MSFT', 'GOOG']     → 科技股
# 社区 2: ['GC=F', 'SI=F']              → 贵金属
# 社区 3: ['XOM', 'CL=F']               → 能源
```

### 模块度 (Modularity) 解读
| 值        | 含义           |
| --------- | -------------- |
| < 0.3     | 社区结构不明显 |
| 0.3 - 0.7 | 中等社区结构   |
| > 0.7     | 强社区结构     |

---

## 典型分析组合

### "A 股市场的板块结构"
```
1. 取沪深300成分股(tushare) → 计算收益率矩阵
2. MST → 核心关系骨架
3. 社区检测 → 自动分组
4. 对比申万行业分类 → 验证聚类合理性
```

### "哪只股票是风险传播的 Hub？"
```
1. 相关性网络 → 度中心性排名
2. 介数中心性 → 信息传导的桥梁
3. MST → 在核心骨架中的位置
```

### "构建分散化组合"
```
1. 社区检测 → 发现聚类
2. 每个社区选代表 → 确保跨社区分散
3. 组合优化 → 在分散基础上优化权重
```
