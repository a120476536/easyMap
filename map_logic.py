import random
import numpy as np
from noise import snoise2  # pip install noise


class MapLogic:
    """负责生成高度图的纯逻辑模块。"""

    def __init__(
        self,
        width: int = 500,
        height: int = 500,
        scale: float = 150.0,
        octaves: int = 8,
        persistence: float = 0.5,
        lacunarity: float = 2.0,
    ) -> None:
        self.width = width
        self.height = height
        self.scale = scale
        self.octaves = octaves
        self.persistence = persistence
        self.lacunarity = lacunarity
        self.seed = random.randint(0, 9999)

    def generate_height_map(self, seed: int | None = None) -> np.ndarray:
        """生成高度图（值域 -1~1），可指定种子。"""
        if seed is not None:
            self.seed = seed

        height_map = np.zeros((self.height, self.width))
        for y in range(self.height):
            for x in range(self.width):
                val = snoise2(
                    y / self.scale,
                    x / self.scale,
                    octaves=self.octaves,
                    persistence=self.persistence,
                    lacunarity=self.lacunarity,
                    base=self.seed,
                )
                height_map[y][x] = val
        return height_map
