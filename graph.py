"""グラフおよびノードを表現するためのモジュール
"""

from typing import Any, NamedTuple

class Edge(NamedTuple):
    """ノード間の辺
    
    あるノードから接続先のノードまでの辺およびノード間の距離を表す

    Attributes:
        dstId: 接続先ノードの ID
        distance: 接続先ノードまでの距離

    Note:
        始点ノードの情報は持たない
    """
    dstId: str
    distance: float

class Node:
    """グラフにおけるノード

    Attributes:
        id: ノード ID
        lat: 緯度
        lon: 経度
        tags (optional): 関連情報
    """

    def __init__(self, nodeId: str, lat: float, lon: float, tags: set[Any] | None = None):
        """
        Args:
            nodeId: ノードを区別するための ID
            lat: 緯度
            lon: 経度
            tags (optional): 関連情報
        """
        self.__nodeId = nodeId
        self.__lat = lat
        self.__lon = lon
        self.__tags : set[Any] = set()
        if tags is not None:
            self.__tags = set(tags)
        self.__adj: list[Edge] = []

    @property
    def id(self) -> str:
        return self.__nodeId

    @property
    def lat(self) -> float:
        return self.__lat

    @property
    def lon(self) -> float:
        return self.__lon

    @property
    def tags(self) -> set[Any]:
        return self.__tags

    def getAdjacents(self) -> list[Edge]:
        """隣接ノードリストを取得する

        Returns:
            このノードに隣接する（接続する）ノードとそこまでの距離
            をEdgeオブジェクトで表し、Edgeのリストを返す
        """
        return self.__adj

    def addAdjacent(self, id: str, distance: float | None):
        """隣接ノードを追加する

        Args:
            id: 隣接ノードの ID
            distance: 隣接ノードまでの距離
        Note:
            既に追加済みの場合は何もしない
        """
        if not self.isExist(id) and distance is not None:
            self.__adj.append(Edge(id, distance)) # node id と node 間の距離を保持する

    def isExist(self, id: str) -> bool:
        """隣接ノードの存在確認

        引数で指定されたノードが、既に隣接ノードとして追加されているか
        否かを判定する

        Args:
            id: 隣接ノードの ID
        Returns:
            True: 追加済み
            False: 追加されていない
        """
        return not (self.getDistance(id) is None)
        
    def getDistance(self, id: str) -> float | None:
        """隣接ノードまでの距離を取得

        Args:
            id: 隣接ノードの ID
        Returns:
            float: 隣接ノードまでの距離
            None: 隣接ノードがない場合
        """
        for item in self.__adj:
            if id == item.dstId:
                return item.distance
        return None

class Graph:
    """グラフ

    グラフに属するノード一覧を保持する

    Attributes:
        size: ノード数
        nodesList (dict[str, Node]): ノード一覧
    Note:
        ノード間の接続状態は、 Node クラスで管理する
    """

    def __init__(self):
        """初期化

        ノード一覧の辞書を初期化する
        """
        self.__nodes : dict[str, Node] = {} # ノード辞書, キー: ノードID, バリュー: node オブジェクト

    @property
    def size(self) -> int:
        return len(self.__nodes)
            
    @property
    def nodesList(self) -> dict[str, Node]:
        return self.__nodes

    def isExist(self, id: str) -> bool:
        """ノードの存在確認

        本グラフが引数で指定されたノードを持つか否か判定

        Returns:
            True: 指定ノードが存在する
            False: 指定ノードは存在しない
        """
        return id in self.__nodes

    def addNode(self, node: Node):
        """グラフへノードを追加

        Args:
            node: Node オブジェクト
        """
        if not (node.id in self.__nodes):
            self.__nodes[node.id] = node

    def get(self, id: str) -> Node | None:
        """ノードを取得

        Args:
            id: ノード ID
        Returns:
            Node: Node オブジェクト
            None: 引数で指定されたノードが存在しない場合
        """
        if id in self.__nodes:
            return self.__nodes[id]
        else:
            return None

    def dump(self):
        """本グラフのノード一覧のダンプ

        本グラフが持つ、すべてのノードについて、各ノードの隣接ノードの
        情報を出力する
        """
        for k in self.__nodes:
            nd: Node = self.__nodes[k]
            print(f"node id: {nd.id}, (lat, lon) =({nd.lat}, {nd.lon})")
            adjList: list[Edge] = nd.getAdjacents()
            for adj in adjList:
                n: Node | None = self.get(adj.dstId)
                if n is not None:
                    print(f"    adj id: {adj.dstId}, (lat, lon) = ({n.lat}, {n.lon}), dist = {adj.distance}")

