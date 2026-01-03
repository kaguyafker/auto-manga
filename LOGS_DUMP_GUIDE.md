# Logs and Dump Channel Feature

## Overview
This feature provides comprehensive logging and backup functionality for the manga bot, allowing the owner to track all bot activities and maintain backups of uploaded files.

## Features

### 1. **Log Channel** 📊
Tracks all bot activities in real-time including:
- User searches (manga queries)
- Download operations
- Upload operations
- Errors and system events
- Admin actions (bans, unbans, settings changes)

### 2. **Dump Channel** 💾
Automatically backs up all uploaded files:
- Stores copies of every manga chapter uploaded
- Includes metadata (manga name, chapter number, timestamp)
- Provides redundancy in case of file loss

## Owner Commands

### Set Log Channel
```
/setlogchannel [channel_id]
```
**Example:** `/setlogchannel -1001234567890`

**Requirements:**
- Bot must be added as admin to the channel
- Channel can be private or public
- Only owner can execute this command

### Remove Log Channel
```
/removelogchannel
```
Disables activity logging.

### Set Dump Channel
```
/setdumpchannel [channel_id]
```
**Example:** `/setdumpchannel -1001234567890`

**Requirements:**
- Bot must be added as admin to the channel
- Channel can be private or public
- Only owner can execute this command

### Remove Dump Channel
```
/removedumpchannel
```
Disables file backups.

### View All Channels
```
/viewchannels
```
Shows configuration for:
- Log Channel
- Dump Channel
- Default Upload Channel

## How to Get Channel ID

1. **Method 1: Forward Message**
   - Forward any message from the channel to [@userinfobot](https://t.me/userinfobot)
   - The bot will show the channel ID

2. **Method 2: Web Telegram**
   - Open the channel in web.telegram.org
   - The URL will contain the channel ID

3. **Method 3: Bot Command**
   - Make the bot admin in the channel
   - The bot can detect the channel ID automatically

## Activity Logging

### What Gets Logged?

#### Search Activities 🔍
```
🔍 SEARCH

Time: 2026-01-03 11:30:45
User: @username (123456789)

Query: One Piece
Sources Available: 4
```

#### Upload Activities ⬆️
```
⬆️ UPLOAD

Time: 2026-01-03 11:35:22
User: @username (123456789)

Manga: One Piece
Chapter: 1050
Source: MangaDex
Pages: 15
File Type: pdf
Target Channel: -1001234567890
```

#### Error Logs ❌
```
❌ ERROR

Time: 2026-01-03 11:40:10
User: @username (123456789)

Failed to download chapter
Error: Connection timeout
```

## Dump Channel Backups

Every uploaded file is automatically backed up to the dump channel with:
- Original file
- Original caption
- Backup timestamp
- "💾 Backup Copy" tag

**Example Caption:**
```
💾 Backup Copy

One Piece - Ch 1050

Backed up: 2026-01-03 11:35:25
```

## Admin Panel Integration

Access channel configuration through:
1. `/settings` command
2. Click "⚙️ Settings"
3. Click "👑 Admin"
4. Click "📺 Channels"

This shows:
- 📊 Log Channel status
- 💾 Dump Channel status
- 📢 Default Upload Channel
- 🤖 Auto-Update Channels

## Security Features

- **Owner-Only Access**: Only the bot owner (USER_ID in config) can manage channels
- **Validation**: Bot verifies it has admin access before saving channel
- **Test Messages**: Sends confirmation message to channel upon setup
- **Error Handling**: Graceful fallback if channels become inaccessible

## Database Storage

Channels are stored in MongoDB:
```javascript
{
  "_id": "log_channel",
  "value": -1001234567890,
  "updated_at": ISODate("2026-01-03T06:00:00Z")
}
```

## Integration with Existing Features

The logging system is integrated into:
- ✅ Search functionality
- ✅ Download operations
- ✅ Upload operations
- ✅ Admin actions (future)
- ✅ Error tracking (future)

## Best Practices

1. **Separate Channels**: Use different channels for logs and dumps
2. **Private Channels**: Keep both channels private for security
3. **Regular Monitoring**: Check log channel daily for issues
4. **Backup Retention**: Periodically archive old dumps
5. **Access Control**: Only give admin access to trusted users

## Troubleshooting

### "Cannot access channel" Error
- Ensure bot is added as admin
- Check channel ID is correct (should start with -100)
- Verify bot has posting permissions

### Logs Not Appearing
- Check if log channel is set: `/viewchannels`
- Verify bot is still admin in the channel
- Check bot has "Post Messages" permission

### Dumps Not Working
- Ensure dump channel is set
- Verify bot has "Send Files" permission
- Check channel storage isn't full

## Performance Impact

- **Minimal**: Logging is asynchronous and non-blocking
- **Storage**: Each log message ~200-500 bytes
- **Network**: Negligible additional bandwidth
- **Database**: Uses existing MongoDB connection

## Future Enhancements

Planned features:
- 📈 Statistics dashboard
- 🔔 Alert notifications for errors
- 📊 Usage analytics
- 🗂️ Automatic log archiving
- 🔍 Log search functionality

## Support

For issues or questions:
- Contact: @koushik_Sama
- GitHub: [Repository Link]
