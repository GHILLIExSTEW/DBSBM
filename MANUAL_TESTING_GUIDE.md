# 🧪 Manual Testing Guide for Community Engagement Features

## 🚀 **Quick Start Testing**

### **Prerequisites:**
1. Bot is running and connected to Discord
2. Bot has proper permissions in your test server
3. Database is properly configured

---

## 📋 **Test Checklist**

### **✅ Phase 1: Basic Command Testing**

#### **1. Community Discussion Commands**
```bash
# Test /discuss command
/discuss "NFL Season" "Who do you think will win the Super Bowl this year?"

# Expected Result: 
# - Embed with green color
# - Title: "💬 Community Discussion: NFL Season"
# - Description: "Who do you think will win the Super Bowl this year?"
# - Footer: "Started by [Your Name]"
```

#### **2. Content Sharing Commands**
```bash
# Test /funfact command
/funfact "The first Super Bowl was played in 1967 between the Green Bay Packers and Kansas City Chiefs"

# Test /celebrate command
/celebrate "Big Win!" "Just won a 5-leg parlay! 🎉"

# Test /shoutout command
/shoutout @username "Amazing betting analysis yesterday!"
```

#### **3. Community Support Commands**
```bash
# Test /encourage command
/encourage @username "Keep up the great work with your predictions!"

# Test /help_community command
/help_community "Parlay Strategy" "What's the best approach for 3-leg parlays?"

# Test /thanks command
/thanks @username "Helped me understand player props"
```

#### **4. Interactive Commands**
```bash
# Test /poll command
/poll "What's your favorite sport to bet on?" "Football" "Basketball" "Baseball" "Soccer"

# Expected Result:
# - Embed with poll options
# - Numbered reactions (1️⃣, 2️⃣, 3️⃣, 4️⃣) added automatically
```

---

### **✅ Phase 2: Leaderboard & Analytics Testing**

#### **1. Leaderboard Commands**
```bash
# Test /community_leaderboard command
/community_leaderboard

# Test with specific category
/community_leaderboard reactions
/community_leaderboard achievements
/community_leaderboard helpful
```

#### **2. Achievement Commands**
```bash
# Test /my_achievements command
/my_achievements

# Expected Result:
# - Shows your earned achievements
# - Or shows how to earn achievements if none earned
```

#### **3. Community Statistics**
```bash
# Test /community_stats command
/community_stats

# Test with specific days
/community_stats 7
/community_stats 30
```

---

### **✅ Phase 3: Integration Testing**

#### **1. Bet Reaction Testing**
1. Create a bet using existing betting commands
2. React to the bet with different emojis (👍, 🔥, 💪, etc.)
3. Check if reactions are being tracked

#### **2. Cross-Command Integration**
1. Use community commands multiple times
2. Check if achievements are being awarded
3. Verify leaderboard data updates

---

## 🔍 **What to Look For**

### **✅ Success Indicators:**
- Commands respond without errors
- Embeds display correctly with proper colors
- User mentions work properly
- Reactions are added to polls
- Leaderboards show data (even if empty)
- Achievements display correctly

### **❌ Error Indicators:**
- Commands fail to respond
- Database errors in logs
- Missing permissions
- Incorrect embed formatting
- Missing reactions on polls

---

## 📊 **Testing Scenarios**

### **Scenario 1: New User Experience**
1. New user joins server
2. Uses `/discuss` to start first conversation
3. Uses `/funfact` to share knowledge
4. Checks `/my_achievements` (should show none)
5. Uses `/community_leaderboard` (should show empty or others)

### **Scenario 2: Active User Experience**
1. User reacts to multiple bets
2. Uses various community commands
3. Checks achievements (should start earning them)
4. Views leaderboard (should appear in rankings)

### **Scenario 3: Community Building**
1. Multiple users use community commands
2. Users encourage each other
3. Community polls are created and voted on
4. Leaderboards show community activity

---

## 🐛 **Common Issues & Solutions**

### **Issue: Commands not responding**
**Solution:** Check bot permissions and ensure commands are synced

### **Issue: Database errors**
**Solution:** Verify database connection and table creation

### **Issue: Missing reactions on polls**
**Solution:** Check bot has "Add Reactions" permission

### **Issue: Leaderboards show no data**
**Solution:** This is normal for new installations - data builds over time

---

## 📈 **Performance Testing**

### **Load Testing:**
1. Have multiple users use commands simultaneously
2. Test with high-frequency command usage
3. Monitor database performance

### **Stress Testing:**
1. Create many polls in quick succession
2. Have many users react to bets simultaneously
3. Test achievement system with many users

---

## 🎯 **Success Criteria**

### **All tests pass if:**
- ✅ All commands respond correctly
- ✅ Embeds display properly
- ✅ Database operations work
- ✅ Achievements are awarded
- ✅ Leaderboards function
- ✅ No errors in bot logs
- ✅ Community engagement increases

---

## 📝 **Test Report Template**

```
Test Date: [Date]
Tester: [Name]
Bot Version: [Version]

Commands Tested:
- [ ] /discuss
- [ ] /funfact  
- [ ] /celebrate
- [ ] /encourage
- [ ] /help_community
- [ ] /thanks
- [ ] /shoutout
- [ ] /poll
- [ ] /community_leaderboard
- [ ] /my_achievements
- [ ] /community_stats

Issues Found:
- [List any issues]

Recommendations:
- [List recommendations]

Overall Status: ✅ PASS / ❌ FAIL
```

---

## 🚀 **Ready to Test!**

Run the automated test script first:
```bash
python test_community_engagement.py
```

Then follow this manual testing guide to verify the Discord commands work correctly in your server.

**Happy Testing! 🎉** 