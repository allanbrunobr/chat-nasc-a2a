# Chat Navigation Integration Test Guide

## Overview
The chat component has been updated to handle internal navigation within the main application. When the NAI agent returns job listings with links like `[Ver detalhes da vaga](/candidato/vagas/123)`, clicking these links will now navigate the main application behind the chat.

## How It Works

### 1. NAI Agent Response Format
The NAI agent returns job matches with markdown links:
```markdown
🎯 **Desenvolvedor Full Stack**
🏢 Empresa: Tech Solutions
📊 Compatibilidade: 85%
🔗 [Ver detalhes da vaga](/candidato/vagas/123)
```

### 2. Chat Component Updates

#### Link Handling
- Added custom `a` component renderer in ReactMarkdown
- Internal links (starting with `/`) trigger Next.js router navigation
- External links continue to open in new tabs

#### Code Changes
1. **Import Next.js Router**
   ```jsx
   import { useRouter } from "next/navigation";
   ```

2. **Custom Link Renderer**
   ```jsx
   a: ({ node, href, children, ...props }) => {
     const handleLinkClick = (e) => {
       if (href && href.startsWith('/')) {
         e.preventDefault();
         router.push(href);
         onNavigate(); // Optionally minimize chat
       }
     };
     // ... rest of implementation
   }
   ```

3. **Optional Chat Minimization**
   - FloatButton passes `handleMinimizeChat` to Chat component
   - Chat calls this callback when navigating
   - Comment out `onNavigate()` if you want to keep chat open

## Testing Instructions

1. **Start Chat Session**
   - Click the chat button to open the assistant
   - Start a conversation

2. **Request Job Matches**
   - Ask: "Buscar vagas compatíveis com meu perfil"
   - Or: "Mostrar vagas de desenvolvedor"

3. **Test Navigation**
   - Click on any "Ver detalhes da vaga" link
   - The main application should navigate to the job details page
   - Chat will minimize (or stay open if you comment out the onNavigate call)

4. **Verify Behavior**
   - Internal links (`/candidato/vagas/...`) navigate within the app
   - External links still open in new tabs
   - Navigation history works correctly

## Configuration Options

### Keep Chat Open During Navigation
To keep the chat window open when navigating, comment out line 116 in `index.jsx`:
```jsx
// onNavigate();
```

### Custom Navigation Behavior
You can extend the navigation handler to:
- Show loading indicators
- Track analytics events
- Handle specific routes differently

## Troubleshooting

1. **Links Not Working**
   - Verify the NAI agent is returning proper markdown format
   - Check browser console for navigation errors
   - Ensure routes exist in the application

2. **Chat Not Minimizing**
   - Verify `onNavigate` prop is passed from FloatButton to Chat
   - Check that the callback is called in the link handler

3. **Router Not Found**
   - Ensure the component is rendered within Next.js app structure
   - Check that `next/navigation` import is correct for your Next.js version