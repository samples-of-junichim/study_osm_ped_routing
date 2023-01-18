"""OpenStreetMap のデータを取得し、道路ネットワークをグラフとして取得するためのクラス

データの取得は、 OverpassAPI を利用する。
"""
import requests
from urllib.parse import urlencode
from typing import Any, Final, TypeGuard
from geopy.distance import geodesic

# 自分のクラス
from graph import Node, Graph
from shortestpath import Distance, ShortestPath


class OverpassApi:
    """OverpassAPI へのリクエストと道路ネットワークのグラフを作成するクラス
    """
    # OverpassApi URL
    API_URL : Final[str] = "https://overpass-api.de/api/interpreter"
    API_KEY : Final[str] = "data"

    # OverpassApi に投げるクエリ
    #__query = '''
    #        [out:json];
    #        area["name" = "伊勢市"];
    #        way(area)["highway"];
    #        out geom;
    #'''
    API_QUERY : Final[str] = '''
            [out:json]
            [bbox: 34.48756, 136.71216, 34.48906, 136.71424];
            way["highway"];
            out geom;
    '''

    def __init__(self):
        # クエリ文字列を URL エンコード
        self.__param : str = urlencode({OverpassApi.API_KEY: OverpassApi.API_QUERY})

    def getRoadData(self) -> Graph:
        """道路のデータを取得し、グラフを作成する
        """

        # データの取得
        try:
            response = requests.get(OverpassApi.API_URL + "?" + self.__param)

            if response.status_code != requests.codes.ok:
                raise RuntimeError("response is not ok: " + str(response.status_code))
                
        except Exception as err:
            print("Exception raised for getting data by OverpassAPI: " + str(err))
            raise

        # json へ変換
        data : dict[str, Any] = response.json()

        # グラフへ変換
        gr: Graph = self.__convertJsonToGraph(data)
        return gr

    def __convertJsonToGraph(self, data: dict[str, Any]) -> Graph:
        """OverpassAPI から取得した JSON データ（辞書オブジェクト）をグラフに変換

        Args:
            data: JSON データの辞書
        Returns:
            Graph: グラフオブジェクト
        """

        # for debug
        #self.__dumpOverpassJson(data)

        # グラフ
        gr = Graph()

        # ループ
        elements : dict[str, Any] = data["elements"];
        print("number of osm elements: ", len(elements))

        for item in elements:
            if OverpassApi.__isItemDict(item):
                #print("item is ", item) # for debug

                # way のみを処理対象とする
                if item["type"] == "way":
                    way: list[Node] = self.__parseWay(item)
                    self.__addWayToGraph(gr, way)
                else:
                    print("Unexpected osm element: " + item["type"])
                    raise RuntimeError("unexpected osm element: ", item["type"])
        
        return gr
    
    @staticmethod
    def __isItemDict(item: Any) -> TypeGuard[dict[str, Any]]:
        """引数が辞書か否か判定

        Args:
            item: オブジェクト
        Returns:
            True: item が辞書オブジェクトで、キー "type" が存在する
            False: それ以外
        Note:
            返り値をTypeGuard として指定している
        """
        if isinstance(item, dict):
            if "type" in item:
                return True
        return False

    def __parseWay(self, way: dict[str, Any]) -> list[Node]:
        """way をパースする

        Args:
            way: 辞書
        Returns:
            Node のリスト
        """
        nodes = way["nodes"]   # node id のリスト, int  のリスト
        geom = way["geometry"] # kat,lon の辞書のリスト, dict のリスト

        if len(nodes) != len(geom):
            raise RuntimeError("Number of node must be match number of geometry")

        # way 上の node について処理
        ndlist: list[Node] = []
        lastNode: Node | None = None
        for nd, geo in zip(nodes, geom):

            if lastNode is None:
                lastNode = Node(str(nd), geo["lat"], geo["lon"]) # OverpassApi から戻ってくる id は int なので str に変換
                currentNode = lastNode
            else:
                currentNode = Node(str(nd), geo["lat"], geo["lon"])
            ndlist.append(currentNode)

            if lastNode.id != currentNode.id:
                d = self.__calcDistance(lastNode, currentNode)

                lastNode.addAdjacent(currentNode.id, d)
                currentNode.addAdjacent(lastNode.id, d)
            
            lastNode = currentNode

        return ndlist

    def __addWayToGraph(self, gr: Graph, way: list[Node]):
        """パースした way をグラフに追加

        wayを構成するノードを随時グラフに追加する。
        その際に、ノード間の距離も計算して、格納する。

        Args:
            gr: グラフオブジェクト
            way: wayを表す辞書
        """
        # ２点が存在するかどうか
        nd1: Node | None = None
        nd2: Node | None = None

        for nd in way:
            # way の最初のノード
            if nd1 is None:
                nd1 = nd
                if gr.isExist(nd1.id):
                    # グラフに格納済みの node を参照するように切り替え
                    nd1 = gr.get(nd1.id)
                else:
                    # グラフに node を追加
                    gr.addNode(nd1)
                continue

            # 2番目以降のノード
            nd2 = nd

            # 1番目のノードの隣接リストに追加
            nd1.addAdjacent(nd2.id, nd2.getDistance(nd1.id))

            # 2番目のノートをグラフへ登録
            if gr.isExist(nd2.id):
                nd2 = gr.get(nd2.id)
                if nd2 is None:
                    continue
            else:
                gr.addNode(nd2)
                
            # 2番目のノードの隣接リストに追加
            nd2.addAdjacent(nd1.id, nd1.getDistance(nd2.id))

            # nd1を更新
            nd1 = nd2

    def __calcDistance(self, nd1: Node, nd2: Node) -> float:
        """２ノード間の距離を計算する

        ノードの位置情報（緯度経度）を用いて、２点間の距離を求める。

        Args:
            nd1: 一つ目のノード
            nd2: 二つ目のノード
        Returns:
            float: ２ノード間の距離, m 単位

        """
        return geodesic((nd1.lat, nd1.lon), (nd2.lat, nd2.lon)).m

    def __dumpOverpassJson(self, d: dict[Any, Any]) -> None:
        """OverpassAPI から取得した JSON のダンプ
        """
        def printDict(d: dict[Any, Any]):
            for k, v in d.items():
                if isinstance(v, dict):
                    print("key: ", k, ", value: dict")
                    printDict(v)
                elif isinstance(v, list):
                    print("key: ", k, ", value: list")
                    printList(v)
                elif isinstance(v, set):
                    print("key: ", k, ", value: set")
                    printSet(v)
                else:
                    print("key: ", k, ", value: ", v)
        def printList(l: list[Any]):
            for item in l:
                if isinstance(item, dict):
                    print("dict: ")
                    printDict(item)
                elif isinstance(item, list):
                    print("list: ")
                    printList(item)
                elif isinstance(item, set):
                    print("set: ")
                    printSet(item)
                else:
                    print("item: ", l)
        def printSet(s: set[Any]):
            for item in s:
                if isinstance(item, dict):
                    print("dict: ")
                    printDict(item)
                elif isinstance(item, list):
                    print("list: ")
                    printList(item)
                elif isinstance(item, set):
                    print("set: ")
                    printSet(item)
                else:
                    print("item: ", item)
        # 表示
        printDict(d)

if __name__ == "__main__":
    print("test")
    
    api = OverpassApi()
    gr: Graph = api.getRoadData()

    gr.dump()

    print("number of node: ", gr.size)

    print("shortest path")
    dikstra = ShortestPath(gr)
    st_id = "1301959953"
    #ed_id = "1301963286"
    ed_id = "5743469002"

    path: list[Distance] = dikstra.calc(st_id, ed_id)
    for nd in path:
        print(f"node id: {nd.id}, distance: {nd.distance} m")
