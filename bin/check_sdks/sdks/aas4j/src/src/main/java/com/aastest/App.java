package com.aastest;

import org.eclipse.digitaltwin.aas4j.v3.dataformat.DeserializationException;
import org.eclipse.digitaltwin.aas4j.v3.dataformat.SerializationException;
import org.eclipse.digitaltwin.aas4j.v3.dataformat.json.JsonDeserializer;
import org.eclipse.digitaltwin.aas4j.v3.dataformat.json.JsonSerializer;
import org.eclipse.digitaltwin.aas4j.v3.dataformat.xml.XmlDeserializer;
import org.eclipse.digitaltwin.aas4j.v3.dataformat.xml.XmlSerializer;
import org.eclipse.digitaltwin.aas4j.v3.model.Environment;

import org.json.JSONObject;

import java.io.PrintWriter;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.Path;
import java.util.stream.Stream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

import java.io.BufferedWriter;
import java.io.FileWriter;

public class App {
    static JSONObject evaluationResults = new JSONObject();

   static int E_NO_ERROR = 0;
   static int E_INPUT_ERROR = 1;
   static int E_DESERIALIZATION_ERROR = 2;
   static int E_VALIDATION_ERROR = 3;
   static int E_SERIALIZATION_ERROR = 4;
   static int E_OUTPUT_ERROR = 5;


    public static void main(String[] args) {

        String INPUT_DIR = "/test_data";
        try {

            Stream<Path> stream = Files.walk(Paths.get(INPUT_DIR));
            stream
                .filter(Files::isRegularFile)
                .forEach( (Path path) -> {
                    File file = new File(path.toString());
                    String pathSuffix = path.toString().substring(INPUT_DIR.length()+1);
                    JSONObject ret = new JSONObject();
                    Environment env = null;
                    if ( pathSuffix.endsWith(".json")) {
                        try {
                            env = new JsonDeserializer().read(file, StandardCharsets.US_ASCII);
                        } catch (DeserializationException e) {
                            return;
                        } catch (IOException e) {
                            System.out.println(e);
                            System.exit(1);
                        }

                        String serialized;
                        try {
                            serialized = new JsonSerializer().write(env);
                        } catch (SerializationException e) {
                            return;
                        }
                        try {
                            PrintWriter out = new PrintWriter("/out/" + pathSuffix);
                            out.print(serialized);
                            out.close();
                        } catch (IOException ee) {
                            System.out.println(ee);
                            System.exit(1);
                        }
                    } else {
                        try {
                            env = new XmlDeserializer().read(file, StandardCharsets.US_ASCII);
                        } catch (DeserializationException e) {
                            return;
                        } catch (FileNotFoundException e) {
                            System.out.println(e);
                            System.exit(1);
                        }

                        String serialized;
                        try {
                            serialized = new XmlSerializer().write(env);
                        } catch (SerializationException e) {
                            return;
                        }
                        try {
                            PrintWriter out = new PrintWriter("/results/" + pathSuffix);
                            out.print(serialized);
                            out.close();
                        } catch (IOException ee) {
                            System.out.println(ee);
                            System.exit(1);
                        }
                    }
                });
        } catch(IOException e) {
            System.out.println(e);
            System.exit(1);
        }
    }
}