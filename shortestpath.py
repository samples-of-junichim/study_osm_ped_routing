"""グラフの２ノード間の最短経路を求めるモジュール
"""

from dataclasses import dataclass
from graph import Edge, Node, Graph
from heap import HeapNode, Heap

@dataclass
class Distance:
    """始点より、あるノードまでの距離を表すクラス

    Attributes:
        id: 対象となるノードの ID
        distance: 対象となるノードまでの距離, -1 は未初期化を表す
        parent: 対象となるノードに到達する直前のノードの ID
    """
    id: str
    distance: float = -1 # -1: 未初期化を表す
    parent: str | None = None

def _get_val(node: Distance) -> float:
    """Distance クラスを対象とした距離取得関数
    """
    return node.distance
def _dist_comp(nd1: Distance, nd2: Distance) -> bool:
    """Distance クラスを対象とした比較関数
    """
    return nd1.id == nd2.id   
    
class DistHeapNode(HeapNode[Distance]):
    """Distance クラスを持つ HeapNode
    """
    def __init__(self, node: Distance):
        super().__init__(node, _get_val, _dist_comp)

class ShortestPath:
    """最短経路を求めるクラス

    最短経路は、ダイクストラを用いて算出する。
    """

    def __init__(self, gr:Graph):
        """
        Args:
            gr: 最短経路の対象となるグラフ
        """
        self.__gr = gr

    def calc(self, stId: str, edId: str) -> list[Distance]:
        """最短経路の算出

        グラフ上のノードを、始点・終点として指定し、両点を結ぶ最短経路
        を算出する。

        Args:
            stId: 始点のノード ID
            edId: 終点のノード ID
        Returns:
            list[Distance]: 最短経路までのノードのリスト, 始点から終点に向かって並ぶ
        """

        # 距離を初期化
        ds: dict[str, Distance] = {}
        nd: Node | None = None
        for nd in self.__gr.nodesList.values():
            if nd is not None:
                ds[nd.id] = Distance(nd.id, -1, None)

        # 始点を取り出し
        nd: Node | None = self.__gr.get(stId)
        if nd is None:
            raise RuntimeError("Node of stId is missing.", stId)

        ds[nd.id].distance = 0 # 開始点なので、距離 0 で初期化

        h = Heap[DistHeapNode, Distance]()
        dhn: DistHeapNode | None = DistHeapNode(ds[nd.id])
        h.append(dhn)

        # ループ処理
        while (True):
            # ヒープ中の一番近い距離のノードを取り出す
            dhn = h.pop()
            if dhn is None:
                # 到達できない
                raise RuntimeError("Cannot reach destination")
            elif dhn.node.id == edId:
                # 終点に到着
                break

            nd = self.__gr.get(dhn.node.id)
            if nd is None:
                # id に対応するノードが存在しない
                raise RuntimeError("Invalid node id: " + dhn.node.id)

            # 隣接ノードのループ
            adjs: list[Edge] = nd.getAdjacents()
            for edge in adjs:
                # 距離を判定
                dist_cur: Distance = ds[nd.id]
                dist_adj: Distance = ds[edge.dstId]
                if dist_adj.distance < 0:
                    dist_adj.distance = dist_cur.distance + edge.distance
                    dist_adj.parent = nd.id

                    # ヒープに追加
                    h.append(DistHeapNode(dist_adj))
                else:
                    if dist_adj.distance > dist_cur.distance + edge.distance:
                        dist_adj.distance = dist_cur.distance + edge.distance
                        dist_adj.parent = nd.id

                        # 更新したヒープノードより上について再構築
                        h.reconstruct(dist_adj)
        
        # 経路を構築
        result: list[Distance] = []
        id: str | None = edId
        while (id is not None):
            result.append(ds[id])
            id = ds[id].parent

        # 構築した経路を、始点から終点の並びに並び替え
        result.reverse()

        return result
