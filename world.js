class GameMap {
    constructor(tileSize) {
        this.tileSize = tileSize;
        // 0 = Grass, 1 = Wall/Water
        this.grid = [
            [1, 1, 1, 1, 1],
            [1, 0, 0, 0, 1],
            [1, 0, 1, 0, 1],
            [1, 1, 1, 1, 1],
        ];
    }

    draw(ctx) {
        for (let y = 0; y < this.grid.length; y++) {
            for (let x = 0; x < this.grid[y].length; x++) {
                ctx.fillStyle = this.grid[y][x] === 1 ? '#333' : '#7cfc00';
                ctx.fillRect(x * this.tileSize, y * this.tileSize, this.tileSize, this.tileSize);
            }
        }
    }
}
