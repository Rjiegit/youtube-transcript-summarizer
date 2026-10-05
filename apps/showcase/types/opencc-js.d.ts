// opencc-js exposes dictionary subpaths but does not ship declarations for them.
declare module "opencc-js/dict/TSCharacters" {
  const dictionary: string;
  export default dictionary;
}
