const GameMechanics = {
    stats: {
        attack: { level: 1, xp: 0 },
        mining: { level: 1, xp: 0 }
    },

    addXP(skill, amount) {
        this.stats[skill].xp += amount;
        // Check for level up: (Simplified formula)
        let nextLevel = Math.floor(0.1 * Math.sqrt(this.stats[skill].xp));
        if (nextLevel > this.stats[skill].level) {
            this.stats[skill].level = nextLevel;
            console.log(`${skill} leveled up to ${nextLevel}!`);
        }
    }
};