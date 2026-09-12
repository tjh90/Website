package net.tjh90.website.core.recipes;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.JarURLConnection;
import java.net.URISyntaxException;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;

public class RecipesLoader {

  private static final String RECIPES_DIR = "/recipes/";
  private static final String RECIPE_EXT = ".md";
  private static final String FILE_PROTOCOL = "file";
  private static final String JAR_PROTOCOL = "jar";

  private RecipesLoader() {
    // Private constructor to prevent instantiation.
  }

  public static List<Recipe> loadRecipes() {
    List<String> recipePathList = getRecipeMarkdownPaths();

    List<String> recipeContentList =
        recipePathList.stream()
            .map(RecipesLoader::readMarkdownFile)
            .filter(fileContent -> fileContent != null)
            .toList();

    return recipeContentList.stream()
        .map(fileContent -> RecipeParser.parse(fileContent))
        .filter(recipeOpt -> recipeOpt.isPresent())
        .map(recipeOpt -> recipeOpt.get())
        .toList();
  }

  private static List<String> getRecipeMarkdownPaths() {
    URL recipesDirUrl = RecipesLoader.class.getResource(RECIPES_DIR);
    if (recipesDirUrl == null) {
      throw new RecipeException("Recipes directory not found: " + RECIPES_DIR);
    }

    String protocol = recipesDirUrl.getProtocol();
    return switch (protocol) {
      case FILE_PROTOCOL -> listFileRecipes(recipesDirUrl);
      case JAR_PROTOCOL -> listJarRecipes(recipesDirUrl);
      default ->
          throw new RecipeException("Unsupported protocol for recipes directory: " + protocol);
    };
  }

  private static List<String> listFileRecipes(URL recipesDirUrl) {
    List<String> paths = new ArrayList<>();

    try (DirectoryStream<Path> directoryStream = Files.newDirectoryStream(toPath(recipesDirUrl))) {
      for (Path path : directoryStream) {
        String fileName = path.getFileName().toString();
        if (fileName.endsWith(RECIPE_EXT)) {
          paths.add(RECIPES_DIR + fileName);
        }
      }
    } catch (IOException e) {
      throw createRecipeDirException(e);
    }

    return paths;
  }

  private static Path toPath(URL recipesDirUrl) {
    try {
      return Path.of(recipesDirUrl.toURI());
    } catch (URISyntaxException e) {
      throw new RecipeException("Invalid recipes directory URL: " + recipesDirUrl, e);
    }
  }

  private static final RecipeException createRecipeDirException(Throwable cause) {
    return new RecipeException("Failed to read recipes directory: " + RECIPES_DIR, cause);
  }

  private static List<String> listJarRecipes(URL recipesDirUrl) {
    List<String> paths = new ArrayList<>();

    try {
      JarURLConnection connection = (JarURLConnection) recipesDirUrl.openConnection();
      String dirName = connection.getEntryName();

      try (JarFile jarFile = connection.getJarFile()) {
        for (Enumeration<JarEntry> entries = jarFile.entries(); entries.hasMoreElements(); ) {
          JarEntry entry = entries.nextElement();
          String entryName = entry.getName();
          if (isRecipeInDirectory(entryName, dirName)) {
            paths.add("/" + entryName);
          }
        }
      }
    } catch (IOException e) {
      throw createRecipeDirException(e);
    }

    return paths;
  }

  private static boolean isRecipeInDirectory(String entryName, String dirName) {
    return entryName.startsWith(dirName)
        && entryName.endsWith(RECIPE_EXT)
        && entryName.indexOf('/', dirName.length()) < 0;
  }

  private static String readMarkdownFile(String path) {
    try (InputStream is = RecipesLoader.class.getResourceAsStream(path)) {
      if (is == null) {
        throw new RecipeException("Recipe not found: " + path);
      }

      try (BufferedReader br =
          new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
        return br.lines().reduce("", (content, line) -> content + line + "\n");
      }
    } catch (IOException e) {
      throw new RecipeException("Failed to read recipe: " + path, e);
    }
  }
}
