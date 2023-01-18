"""ヒープモジュール
"""

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

T = TypeVar("T")
class HeapNode(Generic[T]):
    """ヒープのノード

    ヒープのノードを表すジェネリクスクラス
    型引数で指定したオブジェクトを本クラスが保持することで、任意のクラスを
    ヒープで扱うことを可能とする。

    Attributes:
        val: ヒープのノードが保持する実際のオブジェクトが持つ値。この値に従ってヒープを構成する。

    Note:
        型引数として任意の型を取ることを可能とするため、コンストラクタにて、型引数から
        値を取得する関数および比較関数も併せて指定する必要がある。
        このため、通常は派生クラスを作成し、そのコンストラクタでこれらの関数を
        バインドして利用する。
    """

    def __init__(self, node: T, func_get_val: Callable[[T], float], func_comp: Callable[[T, T], bool]):
        """初期化

        Args:
            node: ヒープで管理したい型のオブジェクト
            func_get_val: ヒープで管理するオブジェクトから値を取得する関数
            func_comp: ヒープで管理するオブジェクトの比較関数
        """
        self.node: T = node
        self.__func_get_val = func_get_val
        self.__func_comp = func_comp

    @property
    def val(self) -> float:
        return self.__func_get_val(self.node)

    def __eq__(self, other: T) -> bool:
        """比較演算子

        本 HeapNode オブジェクトが保持するオブジェクトの値を比較する
        """
        return self.__func_comp(self.node, other)

HN = TypeVar("HN", bound=HeapNode)
class Heap(Generic[HN, T]): # T は HeapNode の型パラメータと一致することを想定
    """ヒープ

    HeapNode をノードとするヒープ（二進木）を構成する。
    デフォルトでは、 HeapNode#val が最も小さい HeapNode が頂点にくるようなる。
    この挙動は、コンストラクタの comparer に比較関数を渡すことで変更できる。

    Attributes:
        size: ノード数

    Example:
        # テスト用の Node 要素
        @dataclass
        class NodeForTest:
            id: str          # id
            distance: float  # 距離

        def get_distnode_val(v: NodeForTest) -> float:
            return v.distance
        def comp_distnode(v1: NodeForTest, v2: NodeForTest) -> bool:
            return v1.id == v2.id

        # HeapNode の派生クラス
        class MyHeapNode(HeapNode[NodeForTest]):
            def __init__(self, node: NodeForTest):
                super().__init__(node, get_distnode_val, comp_distnode)

        # Heap の比較関数
        def comp(node1: MyHeapNode, node2: MyHeapNode) -> bool:
            return node1.val < node2.val

        h = Heap[MyHeapNode, NodeForTest]()      # 距離が小さいものから取り出す
        #h = Heap[MyHeapNode, NodeForTest](comp) # 距離が大きいものから取り出す
        h.append(MyHeapNode(NodeForTest("1", 8)))
    """

    def __init__(self, comparer: Callable[[HN, HN], bool] | None = None):
        """初期化

        ヒープは１次元リストで管理し、親子関係はインデックスで求める形とする。
        このため、self.__list[0] が常に頂点となる。

        Args:
            comparer: ヒープノードの並び替えのための比較関数
        Notes:
            comparer を指定することでヒープのノードの並び方を指定することができる。
            比較関数の指定がない場合は、 HeapNode#val が小さいノードが
            ヒープ木の頂点にくるように並べる。
        """
        self.__list: list[HN] = []
        if comparer is None:
            self.__func_comp = self.__func_comp_default
        else:
            self.__func_comp = comparer

    @property
    def size(self) -> int:
        return len(self.__list)

    def pop(self) -> HN | None:
        """頂点の HeapNode を取り出す

        本メソッド呼び出しにより、ヒープから頂点の HeapNode は取り除かれ、
        ヒープ木が再構成される。

        Returns:
            HeapNode: 頂点がある場合
            None: ヒープ内に HeapNode がない場合
        """
        if len(self.__list) == 0:
            return None
        if len(self.__list) == 1:
            return self.__list.pop(0)

        out: HN = self.__list[0]
        self.__list[0] = self.__list.pop() # ヒープの最後のノードを頂点に移動

        # 頂点から再構築
        self.__reconstruct_topdown()

        return out

    def append(self, target: HN) -> None:
        """ヒープノードを追加

        ヒープにノードを追加し、ヒープを再構築する。

        Args:
            target: ヒープに追加したい HeapNode オブジェクト
        """
        if target is None:
            return
        self.__list.append(target)

        # ヒープ再構築
        self.__reconstruct_bottomup()

    def reconstruct(self, target: T, isBottomUp: bool = True) -> None:
        """明示的にヒープを再構築する

        引数で指定されたノードの値が更新された際に呼び出す。
        更新前に比べて、更新後の値の大小、および、どのようにヒープを構成しているか（値の小さいものが頂点か大きいものが頂点か）に
        より、再構築の方向が決まる。

        Args:
            target:
            isBottomUp (optional): True, 変更したノードから上を再構築（デフォルト）, False, 変更したノードから下を再構築

        Note:
            再構築の向きは ノードの値がどのように変更されたか および どのようにヒープを構成しているかで決まる。
            具体的には次の通り。

            ヒープの構成方法
              * 頂点に val が小さいノードがくる
                - 値が小さくなった場合: isBottomUp -> True
                - 値が大きくなった場合: isBottomUp -> False
              * 頂点に val が大きいノードがくる
                - 値が小さくなった場合: isBottomUp -> False
                - 値が大きくなった場合: isBottomUp -> True
        """
        if target is None:
            return

        # 引数で指定されたノードの位置を探索
        idx: int = -1
        for i in range(len(self.__list)):
            item = self.__list[i]
            if item == target:
                idx = i
                break
        
        # ノードを再構築する方向を切り替え
        if isBottomUp:
            # 指定されたノードより上を再構築
            self.__reconstruct_bottomup_raw(idx)
        else:
            # 指定されたノードより下を再構築
            self.__reconstruct_topdown_raw(idx)
        
    def __func_comp_default(self, node1: HN, node2: HN) -> bool:
        """デフォルトの比較関数

        Returns:
            True: node1 > node2 が成立（node2 のほうが値が小さい）
            False: node1 > node2 が成立しない

        Note:
            この関数が True を返すときに、 node の入れ替えがおこなわれる
        """
        return node1.val > node2.val

    def __reconstruct_bottomup(self):
        """ボトムアップでヒープを再構築
        """
        if len(self.__list) <= 1:
            return
        self.__reconstruct_bottomup_raw(len(self.__list) - 1)

    def __reconstruct_bottomup_raw(self, idx: int):
        """ボトムアップでヒープを再構築

        Args:
            idx: ヒープを保持するリストのidx
        """
        if idx < 0:
            return

        while (True):
            idx_p: int = int(idx / 2 - 1 if idx % 2 == 0 else (idx + 1) / 2 - 1)
            if idx_p < 0:
                break

            if self.__func_comp(self.__list[idx_p], self.__list[idx]):
                # 入れ替え
                self.__swapNode(idx_p, idx)
                idx = idx_p
            else:
                break

    def __reconstruct_topdown(self):
        """トップダウンでヒープを再構築
        """
        if len(self.__list) <= 1:
            return
        self.__reconstruct_topdown_raw(0)

    def __reconstruct_topdown_raw(self, idx: int):
        """トップダウンでヒープを再構築

        Args:
            idx: ヒープを保持するリストのidx
        """
        if idx < 0:
            return

        while (True):
            idx_l: int | None = (idx + 1) * 2 - 1
            idx_r: int | None = (idx + 1) * 2

            if idx_l > len(self.__list) - 1:
                idx_l = None
            if idx_r > len(self.__list) - 1:
                idx_r = None

            if idx_l is None:
                if idx_r is None:
                    break
                else:
                    # idx_l is None and idx_r is not None はヒープの構成上ありえない
                    raise RuntimeError("Logical Error: check heap algorithum.")

            if idx_r is not None:
                # 右の子ノードがある場合
                #   __func_comp が True のほう（デフォルトだと,より val の小さいほう）を選択
                if self.__func_comp(self.__list[idx_r], self.__list[idx_l]):
                    tmpidx = idx_l
                else:
                    tmpidx = idx_r

                # 比較
                if self.__func_comp(self.__list[idx], self.__list[tmpidx]):
                    # 入れ替え
                    self.__swapNode(idx, tmpidx)
                    idx = tmpidx
                else:
                    break
            elif idx_r is None:
                # 右の子ノードがない場合
                if self.__func_comp(self.__list[idx], self.__list[idx_l]):
                    # 入れ替え
                    self.__swapNode(idx, idx_l)
                    idx = idx_l
                else:
                    break

    def __swapNode(self, idx1: int, idx2: int) -> None:
        """ヒープノードの入れ替え
        """
        tmp: HN = self.__list[idx1]
        self.__list[idx1] = self.__list[idx2]
        self.__list[idx2] = tmp

    def dump(self) -> None:
        """ヒープのダンプ
        """
        if len(self.__list) <= 0:
            print("no node")
            return

        for idx in range(len(self.__list)):
            print(f"node: {self.__list[idx].node}, val: {self.__list[idx].val}")


if __name__ == "__main__":
    print("heap test")

    # テスト用の Node 要素
    @dataclass
    class NodeForTest:
        id: str          # id
        distance: float  # 距離

    def get_distnode_val(v: NodeForTest) -> float:
        return v.distance
    def comp_distnode(v1: NodeForTest, v2: NodeForTest) -> bool:
        return v1.id == v2.id

    class MyHeapNode(HeapNode[NodeForTest]):

        def __init__(self, node: NodeForTest):
            super().__init__(node, get_distnode_val, comp_distnode)

    def comp(node1: MyHeapNode, node2: MyHeapNode) -> bool:
        return node1.val < node2.val

    h = Heap[MyHeapNode, NodeForTest]()      # 距離が小さいものから取り出す
    #h = Heap[MyHeapNode, NodeForTest](comp) # 距離が大きいものから取り出す

    h.append(MyHeapNode(NodeForTest("1", 8)))
    h.append(MyHeapNode(NodeForTest("2", 5)))
    testnode: NodeForTest = NodeForTest("10", 15)
    h.append(MyHeapNode(testnode))
    h.append(MyHeapNode(NodeForTest("3", 7)))
    h.append(MyHeapNode(NodeForTest("4", 3)))
    h.append(MyHeapNode(NodeForTest("5", 10)))
    h.append(MyHeapNode(NodeForTest("6", 9)))
    h.append(MyHeapNode(NodeForTest("7", 6)))
    h.append(MyHeapNode(NodeForTest("8", 1)))
    h.append(MyHeapNode(NodeForTest("9", 20)))
    h.append(MyHeapNode(NodeForTest("11", 18)))
    h.append(MyHeapNode(NodeForTest("12", 16)))

    h.dump()
    print("heap size: ", h.size)

#    print("heap sorted")
#    while (True):
#        hn = h.pop()
#        if hn is None:
#            break
#        if isinstance(hn, MyHeapNode):
#            print(f"Node id: {hn.node.id}, dist: {hn.val}")

    # 変更した場合
    print("heap test for reconstruct")

    # 距離が小さいものが頂点のヒープ
    #   値が大きくなる、15 -> 21
    #testnode.distance = 21
    #h.reconstruct(testnode, False)
    #   値が小さくなる、15 -> 4
    testnode.distance = 4
    h.reconstruct(testnode)

    # 距離が大きいものが頂点のヒープ
    #   値が大きくなる、15 -> 21
    #testnode.distance = 21
    #h.reconstruct(testnode)
    #   値が小さくなる、15 -> 4
    #testnode.distance = 4
    #h.reconstruct(testnode, False)

    h.dump()
    print("heap sorted")
    while (True):
        hn = h.pop()
        if hn is None:
            break
        if isinstance(hn, MyHeapNode):
            print(f"Node id: {hn.node.id}, dist: {hn.val}")
