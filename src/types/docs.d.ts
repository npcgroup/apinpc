declare module '*.md' {
  const content: string;
  export default content;
}

declare module '@/docs/*' {
  const content: any;
  export default content;
} 